"""
Database backup and disaster recovery management commands.

This module provides comprehensive backup, recovery, and disaster recovery
procedures for production database management.
"""

import os
import gzip
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection
import subprocess
import json

logger = logging.getLogger('card_limit_system')

class BackupManager:
    """
    Comprehensive backup management system.
    """
    
    def __init__(self):
        self.backup_config = getattr(settings, 'BACKUP_CONFIG', {})
        self.backup_dir = Path(self.backup_config.get('backup_location', '/backup/hdfc/card_limit_system/'))
        self.encryption_enabled = self.backup_config.get('encryption_enabled', True)
        self.compression_enabled = self.backup_config.get('compression_enabled', True)
        self.retention_days = self.backup_config.get('retention_days', 30)
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup types
        self.database_dir = self.backup_dir / 'database'
        self.media_dir = self.backup_dir / 'media'
        self.logs_dir = self.backup_dir / 'logs'
        
        for dir_path in [self.database_dir, self.media_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def create_database_backup(self, backup_type: str = 'full') -> Dict[str, Any]:
        """
        Create database backup using Oracle Data Pump.
        
        Args:
            backup_type: 'full', 'incremental', or 'schema'
        
        Returns:
            Backup metadata
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"database_{backup_type}_{timestamp}"
        
        logger.info(f"Starting {backup_type} database backup: {backup_name}")
        
        try:
            if backup_type == 'full':
                result = self._create_full_database_backup(backup_name)
            elif backup_type == 'incremental':
                result = self._create_incremental_backup(backup_name)
            elif backup_type == 'schema':
                result = self._create_schema_backup(backup_name)
            else:
                raise ValueError(f"Invalid backup type: {backup_type}")
            
            # Create metadata file
            metadata = {
                'backup_name': backup_name,
                'backup_type': backup_type,
                'timestamp': timestamp,
                'size_bytes': result.get('size_bytes', 0),
                'duration_seconds': result.get('duration_seconds', 0),
                'status': 'completed',
                'files': result.get('files', []),
                'checksum': result.get('checksum'),
            }
            
            metadata_file = self.database_dir / f"{backup_name}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Database backup completed: {backup_name}")
            return metadata
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    def _create_full_database_backup(self, backup_name: str) -> Dict[str, Any]:
        """Create full database backup using expdp."""
        start_time = datetime.now()
        dump_file = f"{backup_name}.dmp"
        log_file = f"{backup_name}.log"
        
        # Oracle Data Pump export command
        expdp_cmd = [
            'expdp',
            f"{os.environ.get('DB_USER')}/{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_NAME')}",
            f'directory=DATA_PUMP_DIR',
            f'dumpfile={dump_file}',
            f'logfile={log_file}',
            'schemas=card_limit_user',
            'compression=all',
            'encryption=all',
            'encryption_password=backup_encryption_key'
        ]
        
        try:
            # Run export
            result = subprocess.run(
                expdp_cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                raise CommandError(f"expdp failed: {result.stderr}")
            
            # Move files to backup directory
            source_dump = Path('/u01/app/oracle/admin/HDFC/dpdump') / dump_file
            source_log = Path('/u01/app/oracle/admin/HDFC/dpdump') / log_file
            
            dest_dump = self.database_dir / dump_file
            dest_log = self.database_dir / log_file
            
            shutil.move(str(source_dump), str(dest_dump))
            shutil.move(str(source_log), str(dest_log))
            
            # Compress if enabled
            if self.compression_enabled:
                compressed_dump = self._compress_file(dest_dump)
                dest_dump.unlink()  # Remove uncompressed file
                dest_dump = compressed_dump
            
            # Calculate file size and checksum
            size_bytes = dest_dump.stat().st_size
            checksum = self._calculate_checksum(dest_dump)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                'size_bytes': size_bytes,
                'duration_seconds': duration,
                'files': [str(dest_dump), str(dest_log)],
                'checksum': checksum
            }
            
        except subprocess.TimeoutExpired:
            raise CommandError("Database backup timeout")
        except Exception as e:
            raise CommandError(f"Database backup failed: {e}")
    
    def _create_incremental_backup(self, backup_name: str) -> Dict[str, Any]:
        """Create incremental backup using RMAN."""
        start_time = datetime.now()
        
        # RMAN incremental backup script
        rman_script = f"""
        RUN {{
            ALLOCATE CHANNEL ch1 TYPE DISK;
            BACKUP AS COMPRESSED BACKUPSET 
                   INCREMENTAL LEVEL 1 
                   DATABASE 
                   FORMAT '{self.database_dir}/{backup_name}_%U';
            BACKUP CURRENT CONTROLFILE 
                   FORMAT '{self.database_dir}/{backup_name}_controlfile.ctl';
            RELEASE CHANNEL ch1;
        }}
        """
        
        try:
            # Create RMAN script file
            script_file = self.database_dir / f"{backup_name}_rman_script.sql"
            with open(script_file, 'w') as f:
                f.write(rman_script)
            
            # Run RMAN backup
            rman_cmd = ['rman', 'target', '/', '@' + str(script_file)]
            
            result = subprocess.run(
                rman_cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minutes timeout
            )
            
            if result.returncode != 0:
                raise CommandError(f"RMAN backup failed: {result.stderr}")
            
            # Find created backup files
            backup_files = list(self.database_dir.glob(f"{backup_name}_*"))
            total_size = sum(f.stat().st_size for f in backup_files)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                'size_bytes': total_size,
                'duration_seconds': duration,
                'files': [str(f) for f in backup_files],
                'checksum': self._calculate_checksum(backup_files[0]) if backup_files else None
            }
            
        except subprocess.TimeoutExpired:
            raise CommandError("Incremental backup timeout")
        except Exception as e:
            raise CommandError(f"Incremental backup failed: {e}")
    
    def _create_schema_backup(self, backup_name: str) -> Dict[str, Any]:
        """Create schema-only backup."""
        start_time = datetime.now()
        dump_file = f"{backup_name}_schema.dmp"
        log_file = f"{backup_name}_schema.log"
        
        # Schema-only export
        expdp_cmd = [
            'expdp',
            f"{os.environ.get('DB_USER')}/{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_NAME')}",
            f'directory=DATA_PUMP_DIR',
            f'dumpfile={dump_file}',
            f'logfile={log_file}',
            'schemas=card_limit_user',
            'content=metadata_only',
            'compression=all'
        ]
        
        try:
            result = subprocess.run(
                expdp_cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode != 0:
                raise CommandError(f"Schema backup failed: {result.stderr}")
            
            # Move files
            source_dump = Path('/u01/app/oracle/admin/HDFC/dpdump') / dump_file
            source_log = Path('/u01/app/oracle/admin/HDFC/dpdump') / log_file
            
            dest_dump = self.database_dir / dump_file
            dest_log = self.database_dir / log_file
            
            shutil.move(str(source_dump), str(dest_dump))
            shutil.move(str(source_log), str(dest_log))
            
            size_bytes = dest_dump.stat().st_size
            checksum = self._calculate_checksum(dest_dump)
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                'size_bytes': size_bytes,
                'duration_seconds': duration,
                'files': [str(dest_dump), str(dest_log)],
                'checksum': checksum
            }
            
        except Exception as e:
            raise CommandError(f"Schema backup failed: {e}")
    
    def create_media_backup(self) -> Dict[str, Any]:
        """Create media files backup."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"media_{timestamp}"
        
        logger.info(f"Starting media backup: {backup_name}")
        
        try:
            media_root = Path(settings.MEDIA_ROOT)
            if not media_root.exists():
                logger.warning("Media directory does not exist")
                return {'status': 'skipped', 'reason': 'no_media_directory'}
            
            # Create tar archive
            archive_name = f"{backup_name}.tar"
            if self.compression_enabled:
                archive_name += ".gz"
            
            archive_path = self.media_dir / archive_name
            
            if self.compression_enabled:
                with gzip.open(archive_path, 'wb') as gz_file:
                    subprocess.run(
                        ['tar', '-cf', '-', '-C', str(media_root.parent), media_root.name],
                        stdout=gz_file,
                        check=True
                    )
            else:
                subprocess.run(
                    ['tar', '-cf', str(archive_path), '-C', str(media_root.parent), media_root.name],
                    check=True
                )
            
            size_bytes = archive_path.stat().st_size
            checksum = self._calculate_checksum(archive_path)
            
            metadata = {
                'backup_name': backup_name,
                'backup_type': 'media',
                'timestamp': timestamp,
                'size_bytes': size_bytes,
                'files': [str(archive_path)],
                'checksum': checksum,
                'status': 'completed'
            }
            
            logger.info(f"Media backup completed: {backup_name}")
            return metadata
            
        except Exception as e:
            logger.error(f"Media backup failed: {e}")
            raise
    
    def create_logs_backup(self) -> Dict[str, Any]:
        """Create application logs backup."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"logs_{timestamp}"
        
        logger.info(f"Starting logs backup: {backup_name}")
        
        try:
            log_dirs = [
                '/var/log/hdfc/',
                '/var/log/nginx/',
                '/var/log/supervisor/'
            ]
            
            archive_name = f"{backup_name}.tar"
            if self.compression_enabled:
                archive_name += ".gz"
            
            archive_path = self.logs_dir / archive_name
            
            # Create archive of all log directories
            tar_cmd = ['tar', '-cf', str(archive_path)]
            
            if self.compression_enabled:
                tar_cmd = ['tar', '-czf', str(archive_path)]
            
            for log_dir in log_dirs:
                if Path(log_dir).exists():
                    tar_cmd.extend(['-C', '/', log_dir.lstrip('/')])
            
            subprocess.run(tar_cmd, check=True)
            
            size_bytes = archive_path.stat().st_size
            checksum = self._calculate_checksum(archive_path)
            
            metadata = {
                'backup_name': backup_name,
                'backup_type': 'logs',
                'timestamp': timestamp,
                'size_bytes': size_bytes,
                'files': [str(archive_path)],
                'checksum': checksum,
                'status': 'completed'
            }
            
            logger.info(f"Logs backup completed: {backup_name}")
            return metadata
            
        except Exception as e:
            logger.error(f"Logs backup failed: {e}")
            raise
    
    def restore_database_backup(self, backup_name: str, 
                              restore_type: str = 'full') -> Dict[str, Any]:
        """
        Restore database from backup.
        
        Args:
            backup_name: Name of backup to restore
            restore_type: 'full', 'schema_only', or 'data_only'
        
        Returns:
            Restore operation metadata
        """
        logger.info(f"Starting database restore: {backup_name}")
        
        try:
            # Find backup files
            metadata_file = self.database_dir / f"{backup_name}_metadata.json"
            if not metadata_file.exists():
                raise CommandError(f"Backup metadata not found: {backup_name}")
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            backup_files = metadata.get('files', [])
            dump_file = None
            
            for file_path in backup_files:
                if file_path.endswith('.dmp') or file_path.endswith('.dmp.gz'):
                    dump_file = Path(file_path)
                    break
            
            if not dump_file or not dump_file.exists():
                raise CommandError(f"Backup dump file not found: {backup_name}")
            
            # Decompress if needed
            if dump_file.suffix == '.gz':
                decompressed_file = dump_file.with_suffix('')
                with gzip.open(dump_file, 'rb') as gz_file:
                    with open(decompressed_file, 'wb') as out_file:
                        shutil.copyfileobj(gz_file, out_file)
                dump_file = decompressed_file
            
            # Prepare import command
            import_file = dump_file.name
            log_file = f"restore_{backup_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            
            impdp_cmd = [
                'impdp',
                f"{os.environ.get('DB_USER')}/{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_NAME')}",
                f'directory=DATA_PUMP_DIR',
                f'dumpfile={import_file}',
                f'logfile={log_file}',
                'schemas=card_limit_user',
                'table_exists_action=replace'
            ]
            
            if restore_type == 'schema_only':
                impdp_cmd.append('content=metadata_only')
            elif restore_type == 'data_only':
                impdp_cmd.append('content=data_only')
            
            # Copy dump file to Oracle directory
            oracle_dump_dir = Path('/u01/app/oracle/admin/HDFC/dpdump')
            oracle_dump_file = oracle_dump_dir / import_file
            shutil.copy2(str(dump_file), str(oracle_dump_file))
            
            try:
                # Run import
                start_time = datetime.now()
                result = subprocess.run(
                    impdp_cmd,
                    capture_output=True,
                    text=True,
                    timeout=7200  # 2 hours timeout
                )
                
                duration = (datetime.now() - start_time).total_seconds()
                
                if result.returncode != 0:
                    raise CommandError(f"Database restore failed: {result.stderr}")
                
                restore_metadata = {
                    'backup_name': backup_name,
                    'restore_type': restore_type,
                    'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
                    'duration_seconds': duration,
                    'status': 'completed',
                    'log_output': result.stdout
                }
                
                logger.info(f"Database restore completed: {backup_name}")
                return restore_metadata
                
            finally:
                # Cleanup temporary files
                if oracle_dump_file.exists():
                    oracle_dump_file.unlink()
                if dump_file.name.startswith('decompressed_'):
                    dump_file.unlink()
            
        except subprocess.TimeoutExpired:
            raise CommandError("Database restore timeout")
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            raise
    
    def list_backups(self, backup_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available backups."""
        backups = []
        
        for metadata_file in self.database_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                if backup_type and metadata.get('backup_type') != backup_type:
                    continue
                
                backups.append(metadata)
                
            except Exception as e:
                logger.error(f"Error reading backup metadata {metadata_file}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return backups
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """Remove old backups based on retention policy."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_backups = []
        deleted_size = 0
        
        logger.info(f"Cleaning up backups older than {self.retention_days} days")
        
        for metadata_file in self.database_dir.glob("*_metadata.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                backup_date = datetime.strptime(metadata['timestamp'], '%Y%m%d_%H%M%S')
                
                if backup_date < cutoff_date:
                    # Delete backup files
                    for file_path in metadata.get('files', []):
                        file_path_obj = Path(file_path)
                        if file_path_obj.exists():
                            deleted_size += file_path_obj.stat().st_size
                            file_path_obj.unlink()
                    
                    # Delete metadata file
                    metadata_file.unlink()
                    deleted_backups.append(metadata['backup_name'])
                    
            except Exception as e:
                logger.error(f"Error processing backup metadata {metadata_file}: {e}")
        
        cleanup_result = {
            'deleted_backups': deleted_backups,
            'deleted_count': len(deleted_backups),
            'deleted_size_bytes': deleted_size,
            'deleted_size_mb': deleted_size / (1024 * 1024)
        }
        
        logger.info(f"Cleanup completed: {len(deleted_backups)} backups deleted, "
                   f"{deleted_size / (1024 * 1024):.2f} MB freed")
        
        return cleanup_result
    
    def verify_backup_integrity(self, backup_name: str) -> Dict[str, Any]:
        """Verify backup file integrity."""
        logger.info(f"Verifying backup integrity: {backup_name}")
        
        try:
            metadata_file = self.database_dir / f"{backup_name}_metadata.json"
            if not metadata_file.exists():
                return {'status': 'failed', 'reason': 'metadata_not_found'}
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            verification_results = []
            
            for file_path in metadata.get('files', []):
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    verification_results.append({
                        'file': str(file_path_obj),
                        'status': 'missing'
                    })
                    continue
                
                # Verify file size
                current_size = file_path_obj.stat().st_size
                expected_size = metadata.get('size_bytes', 0)
                
                # Verify checksum
                current_checksum = self._calculate_checksum(file_path_obj)
                expected_checksum = metadata.get('checksum')
                
                verification_results.append({
                    'file': str(file_path_obj),
                    'status': 'valid' if current_checksum == expected_checksum else 'corrupted',
                    'size_match': current_size == expected_size,
                    'checksum_match': current_checksum == expected_checksum
                })
            
            all_valid = all(result['status'] == 'valid' for result in verification_results)
            
            return {
                'backup_name': backup_name,
                'status': 'valid' if all_valid else 'corrupted',
                'verification_results': verification_results
            }
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return {'status': 'failed', 'reason': str(e)}
    
    def _compress_file(self, file_path: Path) -> Path:
        """Compress file using gzip."""
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return compressed_path
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        import hashlib
        
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()

# Global backup manager instance
backup_manager = BackupManager()
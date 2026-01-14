import logging
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime

from fastapi import UploadFile, HTTPException


from .base_service import BaseService
from app.database.cosmos import CosmosDBClient
from app.models import (
    VaultExecution,
    VaultCrawlCheckpoint
)

logger = logging.getLogger("contentflow.api.services.vault_execution_service")

class VaultExecutionService(BaseService):
    """Service for managing vault executions"""

    def __init__(self, cosmos: CosmosDBClient, 
                       container_name: str = "vault_executions",
                       exec_locks_container_name: str = "vault_exec_locks",
                       crawl_checkpoints_container_name: str = "vault_crawl_checkpoints"):
        """
        Initialize VaultExecutionService with database connection and configuration.
        Args:
            cosmos (CosmosDBClient): The Cosmos database instance for data persistence.
            container_name (str, optional): The name of the container to use for vault storage. 
                Defaults to "vault_executions".
            exec_locks_container_name (str, optional): The name of the container for vault execution locks.
                Defaults to "vault_exec_locks".
            crawl_checkpoints_container_name (str, optional): The name of the container for vault crawl checkpoints.
                Defaults to "vault_crawl_checkpoints".
        """
        super().__init__(cosmos=cosmos, container_name=container_name)
        self.exec_locks_container_name = exec_locks_container_name
        self.crawl_checkpoints_container_name = crawl_checkpoints_container_name

    async def get_vault_executions(self, vault_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[VaultExecution]:
        """Get vault by ID"""
        
        query = "SELECT * FROM c WHERE c.vault_id = @vault_id"
        parameters = [
            {"name": "@vault_id", "value": vault_id}
        ]
        try:
            if start_date:
                try:
                    start_date_d = datetime.fromisoformat(start_date)
                    query += " AND c.created_at >= @start_date"
                    parameters.append({"name": "@start_date", "value": start_date_d.isoformat()})
                    
                    if end_date:
                        end_date_d = datetime.fromisoformat(end_date)
                        query += " AND c.created_at <= @end_date"
                        parameters.append({"name": "@end_date", "value": end_date_d.isoformat()})
                    
                except ValueError:
                    raise ValueError("Invalid start_date or end_date format. Use ISO format.")
            
            vault_executions = await self.query(query=query, parameters=parameters)
            return [VaultExecution(**ve) for ve in vault_executions] if vault_executions else []
        except Exception as e:
            logger.error(f"Error retrieving vault executions for vault_id {vault_id}: {e}")
            logger.exception(e)
            raise
    
    async def get_vault_crawl_checkpoints(self, vault_id: str) -> Optional[VaultCrawlCheckpoint]:
        """Get vault by ID"""
        query = "SELECT * FROM c WHERE c.vault_id = @vault_id"
        parameters = [{"name": "@vault_id", "value": vault_id}]
        
        vault_checkpoints = await self.query(query=query, parameters=parameters, target_container=self.crawl_checkpoints_container_name)
        return [VaultCrawlCheckpoint(**ve) for ve in vault_checkpoints] if vault_checkpoints else []

    async def delete_vault_executions(self, vault_id: str) -> None:
        """Delete all executions for a given vault ID"""
        query = "SELECT * FROM c WHERE c.vault_id = @vault_id"
        parameters = [{"name": "@vault_id", "value": vault_id}]
        
        vault_executions = await self.query(query=query, parameters=parameters)
        
        for ve in vault_executions:
            await self.delete(ve['id'])
            
    async def delete_vault_crawl_checkpoints(self, vault_id: str) -> None:
        """Delete all crawl checkpoints for a given vault ID"""
        query = "SELECT * FROM c WHERE c.vault_id = @vault_id"
        parameters = [{"name": "@vault_id", "value": vault_id}]
        
        vault_checkpoints = await self.query(query=query, parameters=parameters, target_container=self.crawl_checkpoints_container_name)
        
        for vc in vault_checkpoints:
            await self.delete(vc['id'], target_container=self.crawl_checkpoints_container_name)
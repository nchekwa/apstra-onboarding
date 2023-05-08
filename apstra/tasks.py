#!/usr/bin/python3
# Copyright 2023-present, Artur Zdolinski, Nchekwa.com, All rights reserved.
import logging
logger = logging.getLogger(__name__)

from typing import List, Tuple, Union
from enum import Enum
from time import sleep

class TaskStatus(Enum):
    in_progress = "in_progress"
    initializing = "init"
    failed = "failed"
    succeeded = "succeeded"
    timeout = "timeout"

class Tasks:
    from . import Apstra    
        
    def __init__(self, main_class: Apstra):
        self.apstra = main_class
        self.parameters = main_class.parameters

    def get_all_tasks(self, bp_id: str = None) -> list:
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        return self.apstra.rest.get_json_response(uri=f"/api/blueprints/{bp_id}/tasks").get("items")

    def get_task_by_id(self, task_id: str, bp_id: str = None) -> dict:
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        return self.apstra.rest.get_json_response(uri=f"/api/blueprints/{bp_id}/tasks/{task_id}")

    def get_active_tasks(self, bp_id: str = None) -> list:
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        try:
            resp = self.apstra.rest.get_json_response(f"/api/blueprints/{bp_id}/tasks", params={"filter": "status in ['init', 'in_progress']"})
        except:
            return []
        return resp.get("items")
        
    def has_active_tasks(self, bp_id: str = None) -> bool:
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        if self.get_active_tasks(bp_id):
            return True
        return False

    def is_task_active(self, task_id: str, bp_id: str = None) -> bool:
        if bp_id is None:
            bp_id = self.parameters.active_bp.id
        task = self.get_task_by_id(task_id)
        if task:
            if task["status"] in [TaskStatus.in_progress.value,TaskStatus.initializing.value]:
                return True
            else:
                return False
        else:
            return False        

    def check_until_true(self, lambda_func, timeout = 60, *args, **kwargs):
        delay = 0.1
        while True:
            logger.debug(f"Check task - delay {delay}")
            result = lambda_func(*args, **kwargs)
            sleep(delay)
            if result:
                return True
            delay = min(delay * 2, timeout)
            if delay >= timeout:
                raise TimeoutError("Was not able to finish task process in {delay}")




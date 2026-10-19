#!/bin/bash
# config.sh — Common configuration for deployment and backup scripts

export SERVICE_NAME="expense-telegram-bot"
export DEPLOY_DIR="/opt/${SERVICE_NAME}"
export BACKUP_DATA_DIR="/opt/${SERVICE_NAME}/data"

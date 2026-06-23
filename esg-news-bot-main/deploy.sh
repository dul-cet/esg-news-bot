#!/bin/bash

# 🚀 Quick Deploy Script for ESG News Bot
# Автоматический скрипт для развёртывания бота на сервере

set -e  # Exit on error

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Логирование
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# Конфигурация
# ============================================================================

REPO_URL="${REPO_URL:-https://github.com/yourname/NewsBotESG.git}"
DEPLOY_PATH="${DEPLOY_PATH:-/opt/newsbot}"
VENV_PATH="$DEPLOY_PATH/venv"
SERVICE_NAME="newsbot"
USER="${DEPLOY_USER:-newsbot}"

# ============================================================================
# Проверки перед деплоем
# ============================================================================

echo -e "\n${BLUE}===============================================${NC}"
echo -e "${BLUE}🚀 ESG News Bot Deploy Script${NC}"
echo -e "${BLUE}===============================================${NC}\n"

log_info "Проверка предварительных требований..."

# Проверить Python версию
if ! command -v python3 &> /dev/null; then
    log_error "Python3 не установлен"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
log_success "Python $PYTHON_VERSION найден"

# Проверить git
if ! command -v git &> /dev/null; then
    log_error "Git не установлен"
    exit 1
fi
log_success "Git найден"

# Проверить sudo для установки сервиса
if ! sudo -n true 2>/dev/null; then
    log_warning "Требуется пароль для sudo операций"
fi

# ============================================================================
# Проверить .env файл
# ============================================================================

if [ ! -f "$DEPLOY_PATH/.env" ] && [ ! -f ".env" ]; then
    log_error ".env файл не найден!"
    log_info "Создайте .env файл из .env.example:"
    echo "  cp .env.example .env"
    echo "  # Отредактируйте .env с необходимыми значениями"
    exit 1
fi

log_success ".env файл найден"

# ============================================================================
# 1. Клонирование / обновление репозитория
# ============================================================================

echo -e "\n${BLUE}1. Project Setup${NC}"

if [ -d "$DEPLOY_PATH/.git" ]; then
    log_info "Обновление репозитория..."
    cd "$DEPLOY_PATH"
    git fetch origin
    git reset --hard origin/main
    log_success "Репозиторий обновлён"
else
    log_info "Клонирование репозитория..."
    sudo mkdir -p "$DEPLOY_PATH"
    sudo git clone "$REPO_URL" "$DEPLOY_PATH"
    log_success "Репозиторий клонирован"
fi

# ============================================================================
# 2. Настройка виртуального окружения
# ============================================================================

echo -e "\n${BLUE}2. Python Environment${NC}"

if [ ! -d "$VENV_PATH" ]; then
    log_info "Создание виртуального окружения..."
    python3 -m venv "$VENV_PATH"
    log_success "Виртуальное окружение создано"
else
    log_info "Виртуальное окружение уже существует"
fi

log_info "Активация виртуального окружения..."
source "$VENV_PATH/bin/activate"

log_info "Обновление pip..."
pip install --quiet --upgrade pip setuptools wheel

log_info "Установка зависимостей..."
pip install --quiet -r "$DEPLOY_PATH/requirements.txt"
log_success "Зависимости установлены"

# ============================================================================
# 3. Подготовка .env и конфигурации
# ============================================================================

echo -e "\n${BLUE}3. Configuration${NC}"

if [ -f ".env" ] && [ ! -f "$DEPLOY_PATH/.env" ]; then
    log_info "Копирование .env файла..."
    sudo cp ".env" "$DEPLOY_PATH/.env"
    sudo chmod 600 "$DEPLOY_PATH/.env"
    sudo chown "$USER:$USER" "$DEPLOY_PATH/.env"
    log_success ".env скопирован и защищён"
elif [ ! -f "$DEPLOY_PATH/.env" ]; then
    log_error ".env файл не найден ни в текущей, ни в целевой директории"
    exit 1
fi

# Создать необходимые директории
log_info "Создание директорий..."
sudo mkdir -p "$DEPLOY_PATH/data"
sudo mkdir -p "$DEPLOY_PATH/logs"
sudo mkdir -p /var/lib/newsbot
sudo mkdir -p /var/log/newsbot

# Установить права доступа
log_info "Установка прав доступа..."
sudo chown -R "$USER:$USER" "$DEPLOY_PATH"
sudo chmod 755 "$DEPLOY_PATH/data"
sudo chmod 755 "$DEPLOY_PATH/logs"
log_success "Директории готовы"

# ============================================================================
# 4. Systemd сервис
# ============================================================================

echo -e "\n${BLUE}4. Systemd Service${NC}"

if [ ! -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    log_info "Создание systemd сервиса..."
    sudo tee "/etc/systemd/system/$SERVICE_NAME.service" > /dev/null <<EOF
[Unit]
Description=ESG News Bot Telegram
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DEPLOY_PATH
Environment="PATH=$VENV_PATH/bin"
ExecStart=$VENV_PATH/bin/python $DEPLOY_PATH/main.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/newsbot/newsbot.log
StandardError=append:/var/log/newsbot/newsbot.log

MemoryLimit=512M
CPUQuota=100%

[Install]
WantedBy=multi-user.target
EOF
    log_success "Systemd сервис создан"
else
    log_info "Systemd сервис уже существует"
fi

log_info "Перезагрузка systemd конфигурации..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
log_success "Systemd переконфигурирован"

# ============================================================================
# 5. Запуск бота
# ============================================================================

echo -e "\n${BLUE}5. Starting Bot${NC}"

log_info "Запуск сервиса..."
sudo systemctl restart "$SERVICE_NAME"
sleep 3

if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    log_success "Сервис успешно запущен"
    log_info "Статус:" 
    sudo systemctl status "$SERVICE_NAME" --no-pager | head -10
else
    log_error "Ошибка при запуске сервиса"
    log_info "Просмотрите логи:"
    echo "  sudo journalctl -u $SERVICE_NAME -n 50"
    exit 1
fi

# ============================================================================
# 6. Проверка здоровья
# ============================================================================

echo -e "\n${BLUE}6. Health Check${NC}"

sleep 2

log_info "Проверка БД..."
if [ -f "$DEPLOY_PATH/data/news.db" ]; then
    INTEGRITY=$(sqlite3 "$DEPLOY_PATH/data/news.db" "PRAGMA integrity_check;" 2>/dev/null || echo "error")
    if [[ "$INTEGRITY" == "ok" ]]; then
        log_success "БД целостна"
    else
        log_warning "БД может быть повреждена: $INTEGRITY"
    fi
else
    log_info "БД будет создана при первом запуске"
fi

log_info "Проверка логов на ошибки..."
if grep -i "ERROR\|CRITICAL" /var/log/newsbot/newsbot.log 2>/dev/null | head -5; then
    log_warning "Обнаружены ошибки в логах (см. выше)"
else
    log_success "Критических ошибок не обнаружено"
fi

# ============================================================================
# 7. Настройка резервного копирования
# ============================================================================

echo -e "\n${BLUE}7. Backup Setup${NC}"

BACKUP_SCRIPT="/usr/local/bin/newsbot-backup.sh"
BACKUP_CRON="0 2 * * * $BACKUP_SCRIPT"

if [ ! -f "$BACKUP_SCRIPT" ]; then
    log_info "Создание скрипта резервного копирования..."
    sudo tee "$BACKUP_SCRIPT" > /dev/null <<'EOF'
#!/bin/bash
BACKUP_DIR="/backups/newsbot"
DB_FILE="$DEPLOY_PATH/data/news.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
sqlite3 $DB_FILE ".backup $BACKUP_DIR/news_$TIMESTAMP.db"
tar -czf $BACKUP_DIR/backup_$TIMESTAMP.tar.gz \
  $DB_FILE /var/log/newsbot/

find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete
echo "✅ Backup completed: $TIMESTAMP"
EOF
    sudo chmod +x "$BACKUP_SCRIPT"
    log_success "Скрипт резервного копирования создан"

    if ! grep -q "newsbot-backup" /var/spool/cron/crontabs/root 2>/dev/null; then
        log_info "Добавление в crontab..."
        (sudo crontab -l 2>/dev/null || echo "") | sudo tee /tmp/crontab.tmp > /dev/null
        echo "$BACKUP_CRON" | sudo tee -a /tmp/crontab.tmp > /dev/null
        sudo crontab /tmp/crontab.tmp
        sudo rm /tmp/crontab.tmp
        log_success "Резервное копирование добавлено в crontab"
    fi
else
    log_info "Скрипт резервного копирования уже существует"
fi

# ============================================================================
# Итоговый отчёт
# ============================================================================

echo -e "\n${BLUE}===============================================${NC}"
echo -e "${GREEN}✅ Deploy Successful!${NC}"
echo -e "${BLUE}===============================================${NC}\n"

echo "📊 Статус:"
echo -e "  Service:   ${GREEN}$(sudo systemctl is-active $SERVICE_NAME)${NC}"
echo -e "  Bot path:  ${BLUE}$DEPLOY_PATH${NC}"
echo -e "  Database:  ${BLUE}$DEPLOY_PATH/data/news.db${NC}"
echo -e "  Logs:      ${BLUE}/var/log/newsbot/newsbot.log${NC}"

echo -e "\n📝 Полезные команды:"
echo "  View status:     sudo systemctl status $SERVICE_NAME"
echo "  View logs:       sudo journalctl -u $SERVICE_NAME -f"
echo "  Restart bot:     sudo systemctl restart $SERVICE_NAME"
echo "  Stop bot:        sudo systemctl stop $SERVICE_NAME"
echo "  Start bot:       sudo systemctl start $SERVICE_NAME"

echo -e "\n🔐 Проверить конфигурацию:"
echo "  cat $DEPLOY_PATH/.env"

echo -e "\n📦 Проверить зависимости:"
echo "  source $VENV_PATH/bin/activate"
echo "  pip list"

echo -e "\n📊 Для мониторинга:"
echo "  tail -f /var/log/newsbot/newsbot.log"
echo "  sqlite3 $DEPLOY_PATH/data/news.db \"SELECT COUNT(*) FROM news;\""

echo -e "\n${GREEN}Deploy готов к использованию! 🎉${NC}\n"

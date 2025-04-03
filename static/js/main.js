let socket;
try {
    socket = io({
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
    });

    // Таймер для автоскрытия уведомления
    let errorTimeout = null;

    function displayConnectionError(message) {
        let errorDiv = document.getElementById('connection-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.id = 'connection-error';
            errorDiv.style.position = 'fixed';
            errorDiv.style.bottom = '10px';
            errorDiv.style.left = '10px';
            errorDiv.style.padding = '5px 10px'; // Уменьшили padding
            // errorDiv.style.backgroundColor = 'red'; // Заменяем красный
            errorDiv.style.backgroundColor = '#ffc107'; // Желтый (Bootstrap warning)
            // errorDiv.style.color = 'white'; // Заменяем белый
            errorDiv.style.color = '#333'; // Темный текст для контраста
            errorDiv.style.zIndex = '1000';
            errorDiv.style.borderRadius = '3px'; // Чуть меньше радиус
            errorDiv.style.fontSize = '0.9em'; // Уменьшили шрифт
            errorDiv.style.boxShadow = '0 1px 3px rgba(0,0,0,0.2)'; // Небольшая тень
            errorDiv.style.display = 'none'; // Сначала скрыт
            document.body.appendChild(errorDiv);
        }

        errorDiv.textContent = message;
        errorDiv.style.display = 'block'; // Показываем

        // Очищаем предыдущий таймер, если он был
        if (errorTimeout) {
            clearTimeout(errorTimeout);
        }

        // Устанавливаем таймер для скрытия через 7 секунд
        errorTimeout = setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 7000); // 7000 миллисекунд = 7 секунд
    }

    socket.on('disconnect', (reason) => {
        if (reason === 'io server disconnect') {
             console.log('Server disconnected the socket.');
             // Можно показать другое, менее критичное уведомление о дисконнекте
             // displayConnectionError("Соединение с сервером потеряно.");
        } else {
             // Показываем уведомление при других дисконнектах (например, при попытке переподключения)
             displayConnectionError("Попытка переподключения к чату...");
        }
    });

    socket.on('connect_error', (err) => {
        console.error('Global socket connection error:', err);
        // Теперь выводим менее заметное сообщение
        displayConnectionError("Ошибка подключения к чату. Проверка соединения...");
    });

    // Добавим обработчик успешного переподключения, чтобы скрыть сообщение
    socket.on('reconnect', (attemptNumber) => {
        console.log(`Successfully reconnected after ${attemptNumber} attempts`);
        let errorDiv = document.getElementById('connection-error');
        if (errorDiv) {
             // Можно показать короткое сообщение об успехе и скрыть его
             errorDiv.textContent = "Соединение восстановлено!";
             errorDiv.style.backgroundColor = '#28a745'; // Зеленый (success)
             errorDiv.style.color = 'white';
             errorDiv.style.display = 'block';
             if (errorTimeout) clearTimeout(errorTimeout); // Отменяем предыдущий таймер скрытия
             errorTimeout = setTimeout(() => { errorDiv.style.display = 'none'; }, 3000); // Скрыть через 3 сек
        }
     });

     socket.on('reconnect_failed', () => {
         console.error('Failed to reconnect after multiple attempts.');
         // Показываем постоянное сообщение о неудаче, если переподключение не удалось
         displayConnectionError("Не удалось восстановить соединение с чатом.");
         // Не ставим таймер на скрытие для этого сообщения
         if (errorTimeout) clearTimeout(errorTimeout);
     });


} catch (e) {
    console.error("Failed to initialize Socket.IO:", e);
    displayConnectionError("Ошибка инициализации чата."); // Оставляем это, т.к. это разовая ошибка при загрузке
}

document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('.nav-links a');
    const currentPath = window.location.pathname;

    links.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

});
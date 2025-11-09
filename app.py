
# app.py - сервер с минимальными изменениями
from flask import Flask, render_template, request, jsonify
import speech_recognition
import json
import os
import logging
from threading import Thread
from voice_assistant import (
    person, assistant, translator, ttsEngine, 
    recognizer, microphone, setup_assistant_voice,
    play_voice_assistant_speech, execute_command_with_name,
    commands, init_assistant
)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

init_assistant()

def recognize_audio_data(audio_data):
    """Распознавание речи из аудио данных для веба"""
    try:
        # Сохраняем аудио во временный файл
        temp_file = "temp_voice_input.wav"
        with open(temp_file, "wb") as f:
            f.write(audio_data)
        
        # Распознаем речь
        with speech_recognition.AudioFile(temp_file) as source:
            audio = recognizer.record(source)
            recognized_text = recognizer.recognize_google(audio, language=assistant.recognition_language).lower()
        
        # Удаляем временный файл
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
        return recognized_text
    except speech_recognition.UnknownValueError:
        return None
    except Exception as e:
        logger.error(f"Error recognizing speech: {e}")
        return None

@app.route('/')
def home():
    return """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Голосовой помощник</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            background: #f8f9fa;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .search-container {
            width: 90%;
            max-width: 600px;
            text-align: center;
        }

        .search-box {
            display: flex;
            align-items: center;
            border: 1px solid #dfe1e5;
            border-radius: 24px;
            padding: 12px 20px;
            background: white;
            box-shadow: 0 1px 6px rgba(32, 33, 36, 0.28);
        }

        .search-box:hover {
            box-shadow: 0 2px 8px rgba(32, 33, 36, 0.3);
        }

        .search-icon {
            color: #9aa0a6;
            margin-right: 15px;
            font-size: 16px;
        }

        #search-input {
            flex: 1;
            border: none;
            outline: none;
            font-size: 16px;
            background: transparent;
        }

        #search-input::placeholder {
            color: #9aa0a6;
        }

        .voice-button {
            background: none;
            border: none;
            padding: 8px;
            cursor: pointer;
            border-radius: 50%;
            color: #5f6368;
            transition: background-color 0.2s;
        }

        .voice-button:hover {
            background-color: #f8f9fa;
        }

        .voice-button.listening {
            background-color: #1a73e8;
            color: white;
        }

        .voice-button.listening i {
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        .voice-visualizer {
            margin-top: 20px;
            display: none;
        }

        .visualizer-text {
            color: #5f6368;
            margin-bottom: 15px;
            font-size: 14px;
        }

        .visualizer-bars {
            display: flex;
            justify-content: center;
            align-items: flex-end;
            height: 30px;
            gap: 3px;
        }

        .visualizer-bars .bar {
            width: 4px;
            background: #1a73e8;
            border-radius: 2px;
            animation: soundBar 1.5s infinite ease-in-out;
        }

        .visualizer-bars .bar:nth-child(1) { animation-delay: 0.0s; height: 8px; }
        .visualizer-bars .bar:nth-child(2) { animation-delay: 0.2s; height: 12px; }
        .visualizer-bars .bar:nth-child(3) { animation-delay: 0.4s; height: 16px; }
        .visualizer-bars .bar:nth-child(4) { animation-delay: 0.6s; height: 20px; }
        .visualizer-bars .bar:nth-child(5) { animation-delay: 0.8s; height: 16px; }
        .visualizer-bars .bar:nth-child(6) { animation-delay: 1.0s; height: 12px; }
        .visualizer-bars .bar:nth-child(7) { animation-delay: 1.2s; height: 8px; }

        @keyframes soundBar {
            0%, 100% { transform: scaleY(1); }
            50% { transform: scaleY(1.5); }
        }

        .response-container {
            margin-top: 20px;
            padding: 15px;
            background: white;
            border-radius: 12px;
            border: 1px solid #dfe1e5;
            display: none;
        }

        .loading-dots {
            display: flex;
            gap: 4px;
            justify-content: center;
        }

        .loading-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #1a73e8;
            animation: loadingDot 1.4s ease-in-out infinite both;
        }

        .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
        .loading-dots span:nth-child(2) { animation-delay: -0.16s; }
        .loading-dots span:nth-child(3) { animation-delay: 0s; }

        @keyframes loadingDot {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
    </style>
</head>
<body>
    <div class="search-container">
        <div class="search-box">
            <i class="fas fa-search search-icon"></i>
            <input type="text" id="search-input" placeholder="Спросите меня о чем-нибудь..." autocomplete="off">
            <button id="voice-button" class="voice-button" title="Голосовой поиск">
                <i class="fas fa-microphone"></i>
            </button>
        </div>

        <div class="voice-visualizer" id="voice-visualizer">
            <div class="visualizer-text">Слушаю...</div>
            <div class="visualizer-bars">
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
                <div class="bar"></div>
            </div>
        </div>

        <div class="response-container" id="response-container">
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/js/all.min.js"></script>
    <script>
        class VoiceAssistant {
            constructor() {
                this.isListening = false;
                this.mediaRecorder = null;
                this.audioChunks = [];
                
                this.searchInput = document.getElementById('search-input');
                this.voiceButton = document.getElementById('voice-button');
                this.voiceVisualizer = document.getElementById('voice-visualizer');
                this.responseContainer = document.getElementById('response-container');
                
                this.voiceButton.addEventListener('click', () => this.toggleVoiceSearch());
                this.searchInput.addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') this.handleTextSearch();
                });
            }

            async toggleVoiceSearch() {
                if (this.isListening) {
                    this.stopVoiceSearch();
                } else {
                    await this.startVoiceSearch();
                }
            }

            async startVoiceSearch() {
                try {
                    if (!navigator.mediaDevices) {
                        alert('Ваш браузер не поддерживает запись аудио');
                        return;
                    }

                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    this.mediaRecorder = new MediaRecorder(stream);
                    this.audioChunks = [];

                    this.mediaRecorder.ondataavailable = (event) => {
                        this.audioChunks.push(event.data);
                    };

                    this.mediaRecorder.onstop = async () => {
                        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
                        await this.sendVoiceToServer(audioBlob);
                        stream.getTracks().forEach(track => track.stop());
                    };

                    this.mediaRecorder.start();
                    this.isListening = true;
                    this.voiceButton.classList.add('listening');
                    this.voiceVisualizer.style.display = 'block';
                    this.showResponse('Слушаю...', true);
                    
                    setTimeout(() => {
                        if (this.isListening) {
                            this.stopVoiceSearch();
                        }
                    }, 10000);

                } catch (error) {
                    console.error('Ошибка доступа к микрофону:', error);
                    alert('Не удалось получить доступ к микрофону');
                }
            }

            stopVoiceSearch() {
                if (this.mediaRecorder && this.isListening) {
                    this.mediaRecorder.stop();
                    this.isListening = false;
                    this.voiceButton.classList.remove('listening');
                    this.voiceVisualizer.style.display = 'none';
                }
            }

            async sendVoiceToServer(audioBlob) {
                try {
                    this.showResponse('Обрабатываю голосовой запрос...', true);
                    
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'voice_input.wav');

                    const response = await fetch('/api/voice_input', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();
                    
                    if (result.success) {
                        this.searchInput.value = result.recognized_text || '';
                        this.showResponse(result.response);
                    } else {
                        this.showResponse('Не удалось распознать речь. Попробуйте еще раз.');
                    }

                } catch (error) {
                    console.error('Ошибка отправки голоса:', error);
                    this.showResponse('Ошибка соединения с сервером');
                }
            }

            async handleTextSearch() {
                const query = this.searchInput.value.trim();
                if (!query) return;

                try {
                    this.showResponse('Обрабатываю запрос...', true);
                    
                    const response = await fetch('/api/process_command', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ command: query })
                    });

                    const result = await response.json();
                    
                    if (result.success) {
                        this.showResponse(result.response);
                    } else {
                        this.showResponse(result.message || 'Произошла ошибка');
                    }

                } catch (error) {
                    console.error('Ошибка отправки запроса:', error);
                    this.showResponse('Ошибка соединения с сервером');
                }
            }

            showResponse(message, isLoading = false) {
                if (isLoading) {
                    this.responseContainer.innerHTML = '<div class="loading-dots"><span></span><span></span><span></span></div>';
                } else {
                    this.responseContainer.innerHTML = message;
                }
                this.responseContainer.style.display = 'block';
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            new VoiceAssistant();
        });
    </script>
</body>
</html>"""

# ДОБАВЬ СТАРЫЕ URL ДЛЯ СОВМЕСТИМОСТИ С HTML
@app.route('/api/voice_input', methods=['POST'])
def handle_voice_input():
    """Для голосовых команд из HTML"""
    return handle_command()

@app.route('/api/process_command', methods=['POST'])  
def handle_process_command():
    """Для текстовых команд из HTML"""
    return handle_command()

@app.route('/api/command', methods=['POST'])
def handle_command():
    """Универсальный обработчик команд"""
    try:
        # Голосовая команда
        if 'audio' in request.files:
            audio_file = request.files['audio']
            command_text = recognize_audio_data(audio_file.read())
            if not command_text:
                return jsonify({'success': False, 'error': 'Не распознано'})
        # Текстовая команда
        else:
            data = request.json or {}
            command_text = data.get('command', '').lower()
            if not command_text:
                return jsonify({'success': False, 'error': 'Нет команды'})
        
        # Выполняем команду
        parts = command_text.split(" ")
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        Thread(target=lambda: execute_command_with_name(command, args)).start()
        
        return jsonify({
            'success': True,
            'text': command_text,
            'response': f"Выполняю: {command_text}"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("Запуск голосового помощника...")
    print(f"Ассистент: {assistant.name}")
    print(f"Пользователь: {person.name}")
    print(f"Язык: {assistant.speech_language}")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
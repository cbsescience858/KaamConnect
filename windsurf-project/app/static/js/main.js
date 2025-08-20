// Modern KaamConnect UI Controller
class KaamConnectUI {
    constructor() {
        this.socket = io();
        this.currentLanguage = 'en';
        this.currentChat = null;
        this.notifications = [];
        this.init();
    }

    init() {
        // Initialize i18n first so UI text is correct before binding other events
        const initialLang = window.currentLang || localStorage.getItem('preferred_language') || this.currentLanguage;
        this.applyLanguage(initialLang);

        this.initializeSocketEvents();
        this.initializeUIEvents();
        this.initializeAnimations();
        this.loadNotifications();
    }

    // Socket.IO Event Handlers
    initializeSocketEvents() {
        this.socket.on('new_message', (msg) => this.handleNewMessage(msg));
        this.socket.on('new_application', (data) => this.handleJobApplication(data));
        this.socket.on('notification', (notification) => this.showNotification(notification));
        this.socket.on('connect', () => this.handleConnection());
        this.socket.on('disconnect', () => this.handleDisconnection());
    }

    // UI Event Handlers
    initializeUIEvents() {
        // Notification button
        const notificationBtn = document.getElementById('notificationBtn');
        if (notificationBtn) {
            notificationBtn.addEventListener('click', () => this.toggleNotifications());
        }

        // Form enhancements
        this.enhanceForms();
        
        // Loading states for buttons
        this.initializeButtonLoading();
        
        // Smooth scrolling
        this.initializeSmoothScrolling();
    }

    // Enhanced Chat Functionality
    initializeChat(userId) {
        this.currentChat = userId;
        this.loadMessages(userId);
        this.setupChatUI();
    }

    setupChatUI() {
        const chatInput = document.querySelector('.chat-input input');
        const sendBtn = document.querySelector('.chat-input button');
        
        if (chatInput && sendBtn) {
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendMessage(chatInput.value);
                    chatInput.value = '';
                }
            });
            
            sendBtn.addEventListener('click', () => {
                this.sendMessage(chatInput.value);
                chatInput.value = '';
            });
        }
    }

    sendMessage(message) {
        if (this.currentChat && message.trim()) {
            this.socket.emit('send_message', {
                content: message,
                language: this.currentLanguage,
                recipientId: this.currentChat
            });
            
            // Add message to UI immediately
            this.addMessageToChat({
                content: message,
                senderId: window.current_user?.id,
                timestamp: new Date()
            });
        }
    }

    addMessageToChat(message) {
        const messagesDiv = document.querySelector('.messages');
        if (!messagesDiv) return;

        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.senderId === window.current_user?.id ? 'sent' : 'received'}`;
        
        messageElement.innerHTML = `
            <div class="message-content">${this.escapeHtml(message.content)}</div>
            <div class="message-time">${this.formatTime(message.timestamp)}</div>
        `;
        
        messagesDiv.appendChild(messageElement);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        // Animate new message
        messageElement.style.opacity = '0';
        messageElement.style.transform = 'translateY(20px)';
        setTimeout(() => {
            messageElement.style.transition = 'all 0.3s ease';
            messageElement.style.opacity = '1';
            messageElement.style.transform = 'translateY(0)';
        }, 10);
    }

    handleNewMessage(message) {
        this.addMessageToChat(message);
        this.showNotification({
            title: 'New Message',
            message: `${message.senderName}: ${message.content}`,
            type: 'info'
        });
    }

    // Notification System
    showNotification(notification) {
        const toast = document.getElementById('liveToast');
        const toastTitle = document.getElementById('toastTitle');
        const toastMessage = document.getElementById('toastMessage');
        
        if (toast && toastTitle && toastMessage) {
            toastTitle.textContent = notification.title || 'Notification';
            toastMessage.textContent = notification.message;
            
            // Update icon based on type
            const icon = toast.querySelector('.toast-header i');
            if (icon) {
                icon.className = this.getNotificationIcon(notification.type);
            }
            
            const bsToast = new bootstrap.Toast(toast);
            bsToast.show();
        }
        
        this.updateNotificationCount();
    }

    getNotificationIcon(type) {
        const icons = {
            success: 'fas fa-check-circle text-success',
            error: 'fas fa-exclamation-circle text-danger',
            warning: 'fas fa-exclamation-triangle text-warning',
            info: 'fas fa-info-circle text-info'
        };
        return icons[type] || icons.info;
    }

    updateNotificationCount() {
        const countElement = document.getElementById('notificationCount');
        if (countElement) {
            const unreadCount = this.notifications.filter(n => !n.read).length;
            if (unreadCount > 0) {
                countElement.textContent = unreadCount;
                countElement.style.display = 'block';
            } else {
                countElement.style.display = 'none';
            }
        }
    }

    // Form Enhancements
    enhanceForms() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            // Add loading states
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.add('loading');
                    submitBtn.disabled = true;
                }
            });

            // Enhanced validation
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('blur', () => this.validateField(input));
                input.addEventListener('input', () => this.clearFieldError(input));
            });
        });
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        // Basic validation rules
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            errorMessage = 'This field is required';
        } else if (field.type === 'email' && value && !this.isValidEmail(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        } else if (field.type === 'tel' && value && !this.isValidPhone(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid phone number';
        }

        this.showFieldError(field, isValid, errorMessage);
        return isValid;
    }

    showFieldError(field, isValid, message) {
        field.classList.toggle('is-invalid', !isValid);
        field.classList.toggle('is-valid', isValid && field.value.trim());

        let errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (!isValid && message) {
            if (!errorDiv) {
                errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                field.parentNode.appendChild(errorDiv);
            }
            errorDiv.textContent = message;
        } else if (errorDiv) {
            errorDiv.remove();
        }
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    // Utility Functions
    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    isValidPhone(phone) {
        return /^[\+]?[1-9][\d]{0,15}$/.test(phone.replace(/\s/g, ''));
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Animation Helpers
    initializeAnimations() {
        // Fade in elements on scroll
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);

        document.querySelectorAll('.card, .job-card, .dashboard-stats').forEach(el => {
            observer.observe(el);
        });
    }

    initializeButtonLoading() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-animate')) {
                e.target.style.transform = 'scale(0.98)';
                setTimeout(() => {
                    e.target.style.transform = '';
                }, 150);
            }
        });
    }

    initializeSmoothScrolling() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }

    // Connection Handlers
    handleConnection() {
        this.showNotification({
            title: 'Connected',
            message: 'Real-time features are now active',
            type: 'success'
        });
    }

    handleDisconnection() {
        this.showNotification({
            title: 'Disconnected',
            message: 'Attempting to reconnect...',
            type: 'warning'
        });
    }

    // Job Application Handler
    handleJobApplication(data) {
        this.showNotification({
            title: 'New Job Application',
            message: `Someone applied to your job: ${data.jobTitle}`,
            type: 'info'
        });
    }

    // Language handling
    changeLanguage(lang) {
        this.applyLanguage(lang);
    }

    async applyLanguage(lang) {
        try {
            this.currentLanguage = lang;
            localStorage.setItem('preferred_language', lang);
            this.socket.emit('language_changed', { language: lang });

            const catalog = await this.fetchUICatalog(lang);
            if (catalog) {
                this.applyTranslations(catalog);
                this.updateLanguageSelect(lang);
                this.showNotification({
                    title: 'Language Changed',
                    message: `Interface language updated to ${lang.toUpperCase()}`,
                    type: 'success'
                });
            }
        } catch (e) {
            console.error('Failed to apply language:', e);
        }
    }

    async fetchUICatalog(lang) {
        try {
            const res = await fetch(`/language/ui-catalog/${encodeURIComponent(lang)}`);
            if (!res.ok) return null;
            const data = await res.json();
            return data.catalog || null;
        } catch (e) {
            console.error('Failed to fetch UI catalog:', e);
            return null;
        }
    }

    applyTranslations(catalog) {
        if (!catalog) return;
        // Text nodes
        document.querySelectorAll('[data-i18n-key]').forEach(el => {
            const key = el.getAttribute('data-i18n-key');
            if (!key) return;
            const translated = catalog[key];
            if (translated) {
                el.textContent = translated;
            }
        });

        // Placeholder translations: elements may declare data-i18n-placeholder-key
        document.querySelectorAll('[data-i18n-placeholder-key]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder-key');
            const translated = catalog[key];
            if (translated) {
                el.setAttribute('placeholder', translated);
            }
        });
    }

    updateLanguageSelect(lang) {
        // Sync the navbar language <select> if present
        const langSelect = document.querySelector('form[action*="/language/set"] select[name="language"]');
        if (langSelect) {
            langSelect.value = lang;
        }
    }

    // Load notifications and other data
    loadNotifications() {
        // This would typically fetch from an API
        this.notifications = [];
        this.updateNotificationCount();
    }

    toggleNotifications() {
        // Implementation for notification dropdown
        console.log('Toggle notifications panel');
    }

    loadMessages(userId) {
        // Implementation for loading chat messages
        console.log('Loading messages for user:', userId);
    }
}

// Initialize the application
let kaamConnectUI;

document.addEventListener('DOMContentLoaded', function() {
    kaamConnectUI = new KaamConnectUI();
    
    // Make some functions globally available for backward compatibility
    window.changeLanguage = (lang) => kaamConnectUI.changeLanguage(lang);
    window.initializeChat = (userId) => kaamConnectUI.initializeChat(userId);
    window.sendMessage = (message) => kaamConnectUI.sendMessage(message);
});

// Legacy functions for backward compatibility
function updateLanguageUI(lang) {
    // Update any language-dependent UI elements
    // This would typically involve fetching translated strings
    // and updating the DOM
}

function loadJobs() {
    fetch('/api/jobs')
        .then(response => response.json())
        .then(jobs => {
            const jobsContainer = document.querySelector('.jobs-container');
            jobs.forEach(job => {
                const jobElement = createJobElement(job);
                jobsContainer.appendChild(jobElement);
            });
        });
}

function createJobElement(job) {
    const jobCard = document.createElement('div');
    jobCard.className = 'job-card card';
    jobCard.innerHTML = `
        <div class="card-body">
            <h5 class="card-title">${job.title}</h5>
            <p class="card-text">${job.description}</p>
            <div class="job-details">
                <span class="badge bg-primary">${job.category}</span>
                <span class="badge bg-secondary">${job.location}</span>
            </div>
            <button class="btn btn-primary" onclick="applyToJob(${job.id})">
                Apply
            </button>
        </div>
    `;
    return jobCard;
}

// Worker profile functionality
function updateWorkerTags(tags) {
    fetch('/api/profile/tags', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tags: tags })
    });
}

// Location sharing
function shareLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            position => {
                const { latitude, longitude } = position.coords;
                socket.emit('share_location', {
                    latitude: latitude,
                    longitude: longitude
                });
            },
            error => {
                console.error('Error getting location:', error);
            }
        );
    }
}

// Phone call handling
function initiateCall(phoneNumber) {
    // This would typically involve integrating with a VoIP service
    // For now, just show a confirmation dialog
    if (confirm(`Call ${phoneNumber}?`)) {
        // Implement call logic here
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Initialize any necessary components
    if (current_user) {
        // Check for any pending notifications
        checkNotifications();
        // Load user-specific data
        loadUserData();
    }
});

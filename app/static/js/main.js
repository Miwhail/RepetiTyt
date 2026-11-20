document.addEventListener('DOMContentLoaded', () => {

    const burgerMenu = document.querySelector('.burger-menu');
    const navMenu = document.querySelector('.nav');

    if (burgerMenu && navMenu) {
        burgerMenu.addEventListener('click', () => {
            burgerMenu.classList.toggle('active');
            navMenu.classList.toggle('active');
            
            if (navMenu.classList.contains('active')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });
    }

    const mainSearchBtn = document.getElementById('search-btn');
    const mainSearchInput = document.getElementById('main-search');

    if (mainSearchBtn && mainSearchInput) {
        mainSearchBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const query = mainSearchInput.value.trim();
            if (query) {
                window.location.href = `/catalog/?q=${encodeURIComponent(query)}`;
            } else {
                mainSearchInput.focus();
            }
        });

        mainSearchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                mainSearchBtn.click();
            }
        });
    }

    const tagLinks = document.querySelectorAll('.tags a');
    tagLinks.forEach(tag => {
        tag.addEventListener('click', (e) => {
            e.preventDefault();
            const subject = tag.textContent.trim();
            window.location.href = `/catalog/?q=${encodeURIComponent(subject)}`;
        });
    });

    const catalogSearchInput = document.querySelector('input[name="q"]');
    const tutorsGrid = document.querySelector('.tutors-grid');
    const pagination = document.querySelector('.pagination');

    if (catalogSearchInput && tutorsGrid) {
        let timeout = null;
        
        catalogSearchInput.addEventListener('input', (e) => {
            clearTimeout(timeout);
            const query = e.target.value;
            
            tutorsGrid.style.opacity = '0.5';
            tutorsGrid.style.pointerEvents = 'none';
            tutorsGrid.style.transition = 'opacity 0.2s';

            timeout = setTimeout(() => {
                fetch(`/api/live-search/?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(data => {
                        tutorsGrid.innerHTML = data.html;
                        if (pagination) {
                            pagination.style.display = query.trim() ? 'none' : 'flex';
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка при живом поиске:', error);
                        tutorsGrid.innerHTML = '<p>Произошла ошибка при загрузке данных.</p>';
                    })
                    .finally(() => {
                        tutorsGrid.style.opacity = '1';
                        tutorsGrid.style.pointerEvents = 'auto';
                    });
            }, 300);
        });
    }

    const bookingForm = document.getElementById('booking-form');
    
    if (bookingForm) {
        bookingForm.addEventListener('submit', (e) => {
            const termsCheckbox = document.getElementById('terms');
            const commentField = document.querySelector('textarea[name="comment"]');
            let hasError = false;

            if (termsCheckbox && !termsCheckbox.checked) {
                alert('Необходимо согласиться с правилами отмены и возврата.');
                e.preventDefault();
                hasError = true;
            }

            if (commentField && commentField.value.length > 200) {
                alert('Комментарий не может быть длиннее 200 символов.');
                e.preventDefault();
                hasError = true;
            }

            return !hasError;
        });
    }

    const cancelModal = document.getElementById('cancel-modal');
    const cancelForm = document.getElementById('cancel-form');

    if (cancelModal && cancelForm) {
        document.body.addEventListener('click', function(e) {
            if (e.target && e.target.classList.contains('btn-cancel')) {
                const lessonId = e.target.getAttribute('data-id');
                
                if (lessonId) {
                    cancelForm.action = `/cancel/${lessonId}/`;
                    cancelModal.style.display = 'flex';
                }
            }
        });
    }

    window.closeCancelModal = function() {
        if (cancelModal) {
            cancelModal.style.display = 'none';
        }
    };

});
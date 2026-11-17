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


    const searchBtn = document.querySelector('.search-box .btn-primary');
    const searchInput = document.querySelector('.search-box input');

    if (searchBtn && searchInput) {
        searchBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const query = searchInput.value.trim();
            if (query) {

                console.log(`Ищем репетитора по запросу: ${query}`);

            } else {
                searchInput.focus();
            }
        });

        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchBtn.click();
            }
        });
    }

    const tagLinks = document.querySelectorAll('.tags a');
    tagLinks.forEach(tag => {
        tag.addEventListener('click', (e) => {
            e.preventDefault();
            const subject = tag.textContent.trim();
            if (searchInput) {
                searchInput.value = subject;
                searchInput.focus();
            }
        });
    });
});
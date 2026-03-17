// Hamburger Menu JavaScript - Dedicated File

class HamburgerMenu {
    constructor() {
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupMenu());
        } else {
            this.setupMenu();
        }
    }

    setupMenu() {
        console.log('Setting up hamburger menu...');
        
        // Get elements
        this.hamburgerToggle = document.querySelector('.hamburger-toggle');
        this.mobileNav = document.querySelector('.mobile-nav');
        this.mobileNavClose = document.querySelector('.mobile-nav-close');
        this.mobileNavLinks = document.querySelectorAll('.mobile-nav-link');
        this.mobileMenuBtn = document.getElementById('mobileMenuBtn');
        
        console.log('Elements found:', {
            toggle: !!this.hamburgerToggle,
            nav: !!this.mobileNav,
            close: !!this.mobileNavClose,
            links: this.mobileNavLinks.length,
            mobileBtn: !!this.mobileMenuBtn
        });

        if (!this.mobileNav) {
            console.error('Hamburger menu elements not found!');
            return;
        }

        // Setup event listeners
        this.setupEventListeners();
        
        // Set active link based on current path
        this.setActiveLink();
    }

    setupEventListeners() {
        // Hamburger toggle click (if visible)
        if (this.hamburgerToggle) {
            this.hamburgerToggle.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Hamburger clicked');
                this.toggleMenu();
            });
        }

        // Bottom nav menu button click
        if (this.mobileMenuBtn) {
            this.mobileMenuBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Mobile menu button clicked');
                this.toggleMenu();
            });
        }

        // Close button click
        if (this.mobileNavClose) {
            this.mobileNavClose.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('Close button clicked');
                this.closeMenu();
            });
        }

        // Navigation link clicks
        this.mobileNavLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                console.log('Nav link clicked:', link.textContent);
                // Allow navigation but close menu after a short delay
                setTimeout(() => this.closeMenu(), 100);
            });
        });

        // Escape key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.mobileNav.classList.contains('active')) {
                this.closeMenu();
            }
        });

        // Click outside to close
        document.addEventListener('click', (e) => {
            if (this.mobileNav.classList.contains('active')) {
                const isClickInside = this.mobileNav.contains(e.target) || 
                                    (this.hamburgerToggle && this.hamburgerToggle.contains(e.target)) ||
                                    (this.mobileMenuBtn && this.mobileMenuBtn.contains(e.target));
                
                if (!isClickInside) {
                    this.closeMenu();
                }
            }
        });
    }

    toggleMenu() {
        console.log('Toggling menu, current state:', this.mobileNav.classList.contains('active'));
        
        if (this.mobileNav.classList.contains('active')) {
            this.closeMenu();
        } else {
            this.openMenu();
        }
    }

    openMenu() {
        console.log('Opening menu');
        this.mobileNav.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
        
        // Update hamburger icon if it exists
        if (this.hamburgerToggle) {
            const icon = this.hamburgerToggle.querySelector('.icon');
            if (icon) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            }
        }
    }

    closeMenu() {
        console.log('Closing menu');
        this.mobileNav.classList.remove('active');
        document.body.style.overflow = ''; // Restore scrolling
        
        // Update hamburger icon if it exists
        if (this.hamburgerToggle) {
            const icon = this.hamburgerToggle.querySelector('.icon');
            if (icon) {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        }
    }

    setActiveLink() {
        const currentPath = window.location.pathname;
        console.log('Current path:', currentPath);
        
        this.mobileNavLinks.forEach(link => {
            const href = link.getAttribute('href');
            if (href === currentPath) {
                link.classList.add('active');
                console.log('Active link set:', href);
            } else {
                link.classList.remove('active');
            }
        });
    }
}

// Initialize the hamburger menu
const hamburgerMenu = new HamburgerMenu();

// Export for potential use in other scripts
window.HamburgerMenu = HamburgerMenu;

/* ═══════════════════════════════════════════
   Assessoria Acadêmica — script.js
   ═══════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  // ════════════════════════════════════
  // SMOOTH SCROLL NAVIGATION
  // ════════════════════════════════════
  var navLinks = document.querySelectorAll('.navbar-links a, .footer-col a[href^="#"]');
  navLinks.forEach(function (link) {
    link.addEventListener('click', function (e) {
      var href = this.getAttribute('href');
      if (href.charAt(0) !== '#') return;
      e.preventDefault();
      var target = document.querySelector(href);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
        closeMobileMenu();
      }
    });
  });

  // Internal anchor links (CTAs)
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var href = this.getAttribute('href');
      var target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });


  // ════════════════════════════════════
  // ACTIVE SECTION HIGHLIGHTING
  // ════════════════════════════════════
  var sections = document.querySelectorAll('.hero, .section');
  var navAnchors = document.querySelectorAll('.navbar-links a');

  if ('IntersectionObserver' in window) {
    var sectionObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var id = entry.target.id;
          navAnchors.forEach(function (a) {
            a.classList.toggle('active', a.getAttribute('href') === '#' + id);
          });
        }
      });
    }, { threshold: 0.3, rootMargin: '-72px 0px -40% 0px' });

    sections.forEach(function (section) {
      sectionObserver.observe(section);
    });
  }


  // ════════════════════════════════════
  // NAVBAR SCROLL EFFECT
  // ════════════════════════════════════
  var navbar = document.getElementById('navbar');
  var scrollTicking = false;

  window.addEventListener('scroll', function () {
    if (!scrollTicking) {
      requestAnimationFrame(function () {
        navbar.classList.toggle('scrolled', window.scrollY > 80);
        scrollTicking = false;
      });
      scrollTicking = true;
    }
  });


  // ════════════════════════════════════
  // MOBILE MENU
  // ════════════════════════════════════
  var navToggle = document.getElementById('navToggle');

  function closeMobileMenu() {
    navbar.classList.remove('mobile-open');
    navToggle.classList.remove('open');
  }

  navToggle.addEventListener('click', function () {
    navbar.classList.toggle('mobile-open');
    this.classList.toggle('open');
  });

  // Close on outside click
  document.addEventListener('click', function (e) {
    if (!navbar.contains(e.target)) closeMobileMenu();
  });


  // ════════════════════════════════════
  // PARTICLES (hero only)
  // ════════════════════════════════════
  var particlesContainer = document.getElementById('particles');
  var heroSection = document.getElementById('home');
  var particleCount = 0;
  var MAX_PARTICLES = 15;
  var particlesActive = true;

  function createParticle() {
    if (!particlesActive || particleCount >= MAX_PARTICLES) return;
    var p = document.createElement('div');
    p.className = 'particle';
    var size = Math.random() * 4 + 2;
    var left = Math.random() * 100;
    var delay = Math.random() * 4;
    var duration = Math.random() * 3 + 5;
    p.style.cssText = 'width:' + size + 'px;height:' + size + 'px;left:' + left +
      '%;bottom:-10px;animation-delay:' + delay + 's;animation-duration:' + duration + 's';
    particlesContainer.appendChild(p);
    particleCount++;
    setTimeout(function () {
      if (p.parentNode) { p.parentNode.removeChild(p); particleCount--; }
    }, (delay + duration) * 1000);
  }

  for (var i = 0; i < 10; i++) createParticle();
  var particleInterval = setInterval(createParticle, 2500);

  // Pause particles when hero not visible
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      particlesActive = entries[0].isIntersecting;
    }, { threshold: 0.1 }).observe(heroSection);
  }


  // ════════════════════════════════════
  // SCROLL ANIMATIONS
  // ════════════════════════════════════
  if ('IntersectionObserver' in window) {
    var animObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          animObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.animate-on-scroll').forEach(function (el) {
      animObserver.observe(el);
    });
  }

  // Timeline animation
  if ('IntersectionObserver' in window) {
    var timeline = document.querySelector('.timeline');
    if (timeline) {
      new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) {
          timeline.classList.add('animated');
        }
      }, { threshold: 0.2 }).observe(timeline);
    }
  }


  // ════════════════════════════════════
  // COUNTER ANIMATION (hero stats)
  // ════════════════════════════════════
  var statsAnimated = false;

  function animateCounters() {
    if (statsAnimated) return;
    statsAnimated = true;
    document.querySelectorAll('.stat-number[data-target]').forEach(function (el) {
      var target = parseInt(el.getAttribute('data-target'));
      var duration = 2000;
      var start = 0;
      var startTime = null;

      function step(timestamp) {
        if (!startTime) startTime = timestamp;
        var progress = Math.min((timestamp - startTime) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
        var current = Math.floor(eased * target);
        el.textContent = current.toLocaleString('pt-BR');
        if (progress < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }

  if ('IntersectionObserver' in window) {
    var heroStats = document.querySelector('.hero-stats');
    if (heroStats) {
      new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) animateCounters();
      }, { threshold: 0.5 }).observe(heroStats);
    }
  }


  // ════════════════════════════════════
  // FAQ ACCORDION
  // ════════════════════════════════════
  document.querySelectorAll('.faq-question').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var item = this.parentElement;
      var wasOpen = item.classList.contains('open');

      // Close all
      document.querySelectorAll('.faq-item.open').forEach(function (openItem) {
        openItem.classList.remove('open');
      });

      // Toggle current
      if (!wasOpen) item.classList.add('open');
    });
  });


  // ════════════════════════════════════
  // QR CODE GENERATION
  // ════════════════════════════════════
  var qrGenerated = false;

  function generateQRCodes() {
    if (qrGenerated) return;
    if (typeof QRCode === 'undefined') { drawFallbackQR('qr1'); drawFallbackQR('qr2'); return; }

    try {
      var qr1Container = document.getElementById('qr1').parentElement;
      var qr2Container = document.getElementById('qr2').parentElement;
      qr1Container.innerHTML = '<div id="qr1-code"></div>';
      qr2Container.innerHTML = '<div id="qr2-code"></div>';

      var opts = { width: 136, height: 136, colorDark: '#1a1a2e', colorLight: '#ffffff', correctLevel: QRCode.CorrectLevel.M };

      new QRCode(document.getElementById('qr1-code'), Object.assign({}, opts, {
        text: 'https://wa.me/5543999066267?text=Olá!%20Gostaria%20de%20solicitar%20um%20orçamento.'
      }));
      new QRCode(document.getElementById('qr2-code'), Object.assign({}, opts, {
        text: 'https://wa.me/5518981591286?text=Olá!%20Gostaria%20de%20solicitar%20um%20orçamento.'
      }));
      qrGenerated = true;
    } catch (e) {
      console.warn('QR fallback:', e);
      drawFallbackQR('qr1');
      drawFallbackQR('qr2');
    }
  }

  // Generate QR when contato section enters viewport
  if ('IntersectionObserver' in window) {
    var contatoSection = document.getElementById('contato');
    if (contatoSection) {
      new IntersectionObserver(function (entries) {
        if (entries[0].isIntersecting) generateQRCodes();
      }, { threshold: 0.1 }).observe(contatoSection);
    }
  }

  function drawFallbackQR(canvasId) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !canvas.getContext) return;
    var ctx = canvas.getContext('2d');
    var size = 140;
    canvas.width = size; canvas.height = size;
    var modules = 25;
    var cellSize = size / modules;
    var seed = canvasId === 'qr1' ? 12345 : 67890;
    function seededRandom() { seed = (seed * 16807) % 2147483647; return seed / 2147483647; }
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, size, size);
    ctx.fillStyle = '#1a1a2e';
    for (var r = 0; r < modules; r++) {
      for (var c = 0; c < modules; c++) {
        var inFinder = (r < 7 && c < 7) || (r < 7 && c >= modules - 7) || (r >= modules - 7 && c < 7);
        if (inFinder) {
          var lr = r < 7 ? r : r - (modules - 7);
          var lc = c < 7 ? c : c - (modules - 7);
          if (lr === 0 || lr === 6 || lc === 0 || lc === 6 || (lr >= 2 && lr <= 4 && lc >= 2 && lc <= 4)) {
            ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
          }
        } else if (!(r === 7 || c === 7 || r === modules - 8 || c === modules - 8)) {
          if (seededRandom() > 0.46) ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
        }
      }
    }
    ctx.fillStyle = '#ffffff';
    var ctrSize = cellSize * 5;
    ctx.fillRect((size - ctrSize) / 2, (size - ctrSize) / 2, ctrSize, ctrSize);
    ctx.fillStyle = '#25d366';
    ctx.beginPath();
    ctx.arc(size / 2, size / 2, cellSize * 1.8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold ' + (cellSize * 2) + 'px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('\u2706', size / 2, size / 2 + 1);
  }


  // ════════════════════════════════════
  // HOVER EFFECTS
  // ════════════════════════════════════
  document.querySelectorAll('.card, .contact-card, .step-content, .servico-card').forEach(function (el) {
    el.addEventListener('mouseenter', function () {
      this.style.transition = 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)';
    });
  });

});

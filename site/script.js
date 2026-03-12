/* ═══════════════════════════════════════════
   Assessoria Acadêmica — script.js
   ═══════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {

  // ════════════════════════════════════
  // TAB NAVIGATION
  // ════════════════════════════════════
  var navButtons = document.querySelectorAll('.nav-btn');
  var tabSections = document.querySelectorAll('.tab-section');

  function showTab(tabId) {
    tabSections.forEach(function (section) {
      section.classList.remove('active');
    });

    navButtons.forEach(function (btn) {
      btn.classList.remove('active');
    });

    var target = document.getElementById(tabId);
    if (target) {
      target.classList.add('active');
    }

    navButtons.forEach(function (btn) {
      if (btn.getAttribute('data-tab') === tabId) {
        btn.classList.add('active');
      }
    });

    triggerSectionAnimations(tabId);

    if (tabId === 'orcamento') {
      generateQRCodes();
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  navButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      showTab(this.getAttribute('data-tab'));
    });
  });

  // CTA buttons
  ['btn-orcamento', 'btn-orcamento-2'].forEach(function (id) {
    var el = document.getElementById(id);
    if (el) {
      el.addEventListener('click', function () {
        showTab('orcamento');
      });
    }
  });


  // ════════════════════════════════════
  // SCROLL-TRIGGERED ANIMATIONS
  // ════════════════════════════════════
  function triggerSectionAnimations(tabId) {
    if (tabId === 'apresentacao') animateCards();
    if (tabId === 'como-funciona') animateTimeline();
  }

  function animateCards() {
    document.querySelectorAll('.card').forEach(function (card) {
      card.classList.remove('visible');
      void card.offsetWidth;
      card.classList.add('visible');
    });
  }

  function animateTimeline() {
    var timeline = document.querySelector('.timeline');
    if (timeline) {
      timeline.classList.remove('animated');
      void timeline.offsetWidth;
      timeline.classList.add('animated');
    }

    document.querySelectorAll('.timeline-step').forEach(function (step) {
      step.classList.remove('visible');
      void step.offsetWidth;
      step.classList.add('visible');
    });
  }

  setTimeout(animateCards, 300);


  // ════════════════════════════════════
  // NAVBAR SCROLL EFFECT
  // ════════════════════════════════════
  var navbar = document.getElementById('navbar');
  var scrollTicking = false;

  window.addEventListener('scroll', function () {
    if (!scrollTicking) {
      requestAnimationFrame(function () {
        if (window.scrollY > 10) {
          navbar.classList.add('scrolled');
        } else {
          navbar.classList.remove('scrolled');
        }
        scrollTicking = false;
      });
      scrollTicking = true;
    }
  });


  // ════════════════════════════════════
  // BANNER PARTICLES (optimized)
  // ════════════════════════════════════
  var particlesContainer = document.getElementById('particles');
  var MAX_PARTICLES = 15;
  var particleCount = 0;

  function createParticle() {
    if (particleCount >= MAX_PARTICLES) return;

    var particle = document.createElement('div');
    particle.className = 'particle';

    var size = Math.random() * 4 + 2;
    var left = Math.random() * 100;
    var delay = Math.random() * 4;
    var duration = Math.random() * 3 + 5;

    particle.style.cssText =
      'width:' + size + 'px;height:' + size + 'px;left:' + left +
      '%;bottom:-10px;animation-delay:' + delay + 's;animation-duration:' + duration + 's';

    particlesContainer.appendChild(particle);
    particleCount++;

    setTimeout(function () {
      if (particle.parentNode) {
        particle.parentNode.removeChild(particle);
        particleCount--;
      }
    }, (delay + duration) * 1000);
  }

  for (var i = 0; i < 10; i++) {
    createParticle();
  }

  setInterval(createParticle, 2500);


  // ════════════════════════════════════
  // QR CODE GENERATION
  // ════════════════════════════════════
  var qrGenerated = false;

  function generateQRCodes() {
    if (qrGenerated) return;

    if (typeof QRCode === 'undefined') {
      drawFallbackQR('qr1');
      drawFallbackQR('qr2');
      return;
    }

    try {
      var qr1Container = document.getElementById('qr1').parentElement;
      var qr2Container = document.getElementById('qr2').parentElement;

      qr1Container.innerHTML = '<div id="qr1-code"></div>';
      qr2Container.innerHTML = '<div id="qr2-code"></div>';

      var qrOptions = {
        width: 136,
        height: 136,
        colorDark: '#1a1a2e',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.M
      };

      new QRCode(document.getElementById('qr1-code'), Object.assign({}, qrOptions, {
        text: 'https://wa.me/5543999066267?text=Tenho%20interesse%20em%20extens%C3%B5es'
      }));

      new QRCode(document.getElementById('qr2-code'), Object.assign({}, qrOptions, {
        text: 'https://wa.me/5518981591286?text=Tenho%20interesse%20em%20extens%C3%B5es'
      }));

      qrGenerated = true;
    } catch (e) {
      console.warn('QR Code generation failed, using fallback:', e);
      drawFallbackQR('qr1');
      drawFallbackQR('qr2');
    }
  }

  function drawFallbackQR(canvasId) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !canvas.getContext) return;

    var ctx = canvas.getContext('2d');
    var size = 140;
    canvas.width = size;
    canvas.height = size;

    var modules = 25;
    var cellSize = size / modules;
    var seed = canvasId === 'qr1' ? 12345 : 67890;

    function seededRandom() {
      seed = (seed * 16807 + 0) % 2147483647;
      return seed / 2147483647;
    }

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, size, size);
    ctx.fillStyle = '#1a1a2e';

    for (var r = 0; r < modules; r++) {
      for (var c = 0; c < modules; c++) {
        var inFinder = (r < 7 && c < 7) || (r < 7 && c >= modules - 7) || (r >= modules - 7 && c < 7);

        if (inFinder) {
          var lr = r < 7 ? r : r - (modules - 7);
          var lc = c < 7 ? c : c - (modules - 7);
          var isEdge = lr === 0 || lr === 6 || lc === 0 || lc === 6;
          var isInner = lr >= 2 && lr <= 4 && lc >= 2 && lc <= 4;
          if (isEdge || isInner) {
            ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
          }
        } else if (!(r === 7 || c === 7 || r === modules - 8 || c === modules - 8)) {
          if (seededRandom() > 0.46) {
            ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize);
          }
        }
      }
    }

    ctx.fillStyle = '#ffffff';
    var ctrSize = cellSize * 5;
    var ctrPos = (size - ctrSize) / 2;
    ctx.fillRect(ctrPos, ctrPos, ctrSize, ctrSize);
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
  // INTERSECTION OBSERVER
  // ════════════════════════════════════
  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.card, .timeline-step').forEach(function (el) {
      observer.observe(el);
    });
  }


  // ════════════════════════════════════
  // SMOOTH HOVER EFFECT
  // ════════════════════════════════════
  document.querySelectorAll('.card, .contact-card, .step-content').forEach(function (el) {
    el.addEventListener('mouseenter', function () {
      this.style.transition = 'all 0.35s cubic-bezier(0.4, 0, 0.2, 1)';
    });
  });

});

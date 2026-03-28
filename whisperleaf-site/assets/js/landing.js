(function () {
      var el = document.getElementById('finalCtaOwl');
      if (!el) return;
      el.addEventListener('click', function (e) {
        e.preventDefault();
        var btn = el.querySelector('.final-cta-owl-button');
        if (btn) btn.classList.add('owl-cta-clicked');
        setTimeout(function () { window.location.href = 'downloads/whisperleaf-beta.zip'; }, 120);
      });
    })();

    (function () {
      var modal = document.getElementById('howItWorksModal');
      var seeHowBtn = document.getElementById('seeHowBtn');

      function openHowModal() {
        if (!modal) return;
        modal.classList.remove('hidden');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
      }

      function closeHowModal() {
        if (!modal) return;
        modal.classList.add('hidden');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
      }

      if (seeHowBtn) {
        seeHowBtn.addEventListener('click', function () {
          openHowModal();
        });
      }

      document.querySelectorAll('[data-how-modal-close]').forEach(function (el) {
        el.addEventListener('click', function () {
          closeHowModal();
        });
      });

      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && modal && !modal.classList.contains('hidden')) {
          closeHowModal();
        }
      });
    })();

    (function () {
      var demo = document.getElementById('guided-demo');
      var flow = document.getElementById('guidedDemoFlow');
      if (!demo || !flow) return;
      var steps = Array.prototype.slice.call(flow.querySelectorAll('.guided-step'));
      if (!steps.length) return;

      var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      var activated = false;

      function activateDemo() {
        if (activated) return;
        activated = true;
        steps.forEach(function (step, i) {
          if (reducedMotion) {
            step.classList.add('is-active');
            return;
          }
          setTimeout(function () {
            step.classList.add('is-active');
          }, i * 220);
        });
      }

      if ('IntersectionObserver' in window) {
        var obs = new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            if (entry.isIntersecting) {
              activateDemo();
              obs.disconnect();
            }
          });
        }, { threshold: 0.35 });
        obs.observe(demo);
      } else {
        activateDemo();
      }
    })();

// Custom event tracking for Trading Master
document.addEventListener('DOMContentLoaded', function() {
    // Track quiz submissions
    const quizForms = document.querySelectorAll('form[action*="quiz"]');
    quizForms.forEach(form => {
        form.addEventListener('submit', function() {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'quiz_submission', {
                    'event_category': 'engagement',
                    'event_label': window.location.pathname
                });
            }
        });
    });
    
    // Track bias test selections
    const biasTestLinks = document.querySelectorAll('a[href*="daily_bias"]');
    biasTestLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (typeof gtag !== 'undefined') {
                const assetType = this.getAttribute('href').split('/').pop();
                gtag('event', 'bias_test_started', {
                    'event_category': 'engagement',
                    'event_label': assetType
                });
            }
        });
    });
    
    // Track charting exam interactions
    const chartingExamLinks = document.querySelectorAll('a[href*="charting_exam"]');
    chartingExamLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (typeof gtag !== 'undefined') {
                const examType = this.getAttribute('href').split('/').pop();
                gtag('event', 'charting_exam_started', {
                    'event_category': 'learning',
                    'event_label': examType
                });
            }
        });
    });
    
    // Track study material views
    const studyLinks = document.querySelectorAll('a[href*="study"]');
    studyLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'study_material_viewed', {
                    'event_category': 'learning',
                    'event_label': this.innerText.trim()
                });
            }
        });
    });
});
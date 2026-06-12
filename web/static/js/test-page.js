// ABOUTME: Event handlers for the test/debug page (test.html).
// ABOUTME: Provides toast, loading, keyboard shortcut, and theme change demos.

function testToast(type) {
    const messages = {
        success: 'Operation completed successfully!',
        error: 'Something went wrong. Please try again.',
        warning: 'Please review your input before proceeding.',
        info: 'Here is some helpful information.'
    };

    Utils.showToast(messages[type] || 'Test message', type);
}

function testLoading() {
    const btn = document.getElementById('loading-btn');
    Utils.setLoading(btn, true);

    setTimeout(() => {
        Utils.setLoading(btn, false);
        Utils.showToast('Loading test completed!', 'success');
    }, 3000);
}

document.addEventListener('DOMContentLoaded', () => {
    // Toast test buttons
    document.querySelectorAll('[data-toast]').forEach(btn => {
        btn.addEventListener('click', () => testToast(btn.dataset.toast));
    });

    // Loading test button
    document.getElementById('loading-btn')?.addEventListener('click', testLoading);

    // Test keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (Utils.keyboard.isCombo(e, 'ctrl+k')) {
            e.preventDefault();
            Utils.showToast('Keyboard shortcut Ctrl+K detected!', 'info');
        }
    });

    // Test theme change event
    window.addEventListener('themechange', (e) => {
        Utils.showToast(`Theme changed to ${e.detail.theme}`, 'info', 2000);
    });
});

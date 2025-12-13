/**
 * Feedback Manager (PRD-038)
 * Handles user feedback on synthesis and themes.
 *
 * Features:
 * - Simple thumbs up/down feedback
 * - Detailed feedback modal with star ratings
 * - Toast notifications for feedback confirmation
 * - Accessibility support via AccessibilityManager
 */

const FeedbackManager = {
    // Cache feedback state to show correct button states
    feedbackCache: {},

    /**
     * Initialize feedback manager
     */
    init() {
        this.setupEventDelegation();
        this.setupModalEvents();
        console.log('[Feedback] Manager initialized');
    },

    /**
     * Setup event delegation for dynamically added buttons
     */
    setupEventDelegation() {
        document.addEventListener('click', (e) => {
            const thumbsUpBtn = e.target.closest('[data-feedback-up]');
            const thumbsDownBtn = e.target.closest('[data-feedback-down]');
            const detailedBtn = e.target.closest('[data-feedback-detailed]');

            if (thumbsUpBtn) {
                e.preventDefault();
                const type = thumbsUpBtn.dataset.feedbackType;
                const id = parseInt(thumbsUpBtn.dataset.feedbackId);
                this.submitSimpleFeedback(type, id, true);
            }

            if (thumbsDownBtn) {
                e.preventDefault();
                const type = thumbsDownBtn.dataset.feedbackType;
                const id = parseInt(thumbsDownBtn.dataset.feedbackId);
                this.submitSimpleFeedback(type, id, false);
            }

            if (detailedBtn) {
                e.preventDefault();
                const type = detailedBtn.dataset.feedbackType;
                const id = parseInt(detailedBtn.dataset.feedbackId);
                this.openFeedbackModal(type, id);
            }
        });
    },

    /**
     * Setup modal event handlers
     */
    setupModalEvents() {
        // Close modal on backdrop click
        const modal = document.getElementById('feedback-modal');
        if (modal) {
            const backdrop = modal.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.addEventListener('click', () => this.closeFeedbackModal());
            }
        }
    },

    /**
     * Submit simple thumbs up/down feedback
     */
    async submitSimpleFeedback(type, id, isPositive) {
        const endpoint = `/engagement/${type}/${id}/simple`;

        try {
            const response = await apiFetch(endpoint, {
                method: 'POST',
                body: JSON.stringify({ is_positive: isPositive })
            });

            if (response.status === 'success') {
                // Update cache and UI state
                this.feedbackCache[`${type}-${id}`] = { is_positive: isPositive };
                this.updateFeedbackButtonStates(type, id, isPositive);

                // Show toast
                if (typeof ToastManager !== 'undefined') {
                    ToastManager.success(
                        isPositive ? 'Thanks for the positive feedback!' : 'Thanks for letting us know!',
                        'Feedback Recorded'
                    );
                }

                // Announce to screen readers
                if (typeof AccessibilityManager !== 'undefined') {
                    AccessibilityManager.announce('Feedback submitted successfully');
                }
            }
        } catch (error) {
            console.error('[Feedback] Error submitting:', error);
            if (typeof ToastManager !== 'undefined') {
                ToastManager.error('Failed to submit feedback. Please try again.', 'Error');
            }
        }
    },

    /**
     * Update button states after feedback submission
     */
    updateFeedbackButtonStates(type, id, isPositive) {
        const container = document.querySelector(`[data-feedback-container="${type}-${id}"]`);
        if (!container) return;

        const upBtn = container.querySelector('[data-feedback-up]');
        const downBtn = container.querySelector('[data-feedback-down]');

        if (upBtn) {
            upBtn.classList.toggle('active', isPositive === true);
            upBtn.setAttribute('aria-pressed', isPositive === true);
        }
        if (downBtn) {
            downBtn.classList.toggle('active', isPositive === false);
            downBtn.setAttribute('aria-pressed', isPositive === false);
        }
    },

    /**
     * Open detailed feedback modal
     */
    openFeedbackModal(type, id) {
        const modal = document.getElementById('feedback-modal');
        if (!modal) {
            console.error('[Feedback] Modal not found');
            return;
        }

        // Store context
        modal.dataset.feedbackType = type;
        modal.dataset.feedbackId = id;

        // Reset form
        const form = modal.querySelector('#feedback-form');
        if (form) form.reset();

        // Show appropriate rating fields based on type
        const synthesisRatings = modal.querySelector('#synthesis-ratings');
        const themeRatings = modal.querySelector('#theme-ratings');

        if (synthesisRatings) {
            synthesisRatings.style.display = type === 'synthesis' ? 'block' : 'none';
        }
        if (themeRatings) {
            themeRatings.style.display = type === 'theme' ? 'block' : 'none';
        }

        // Update modal title
        const modalTitle = modal.querySelector('.modal-title');
        if (modalTitle) {
            modalTitle.textContent = type === 'synthesis'
                ? 'Rate This Synthesis'
                : 'Rate This Theme';
        }

        // Load existing feedback if any
        this.loadExistingFeedback(type, id);

        // Open modal
        modal.classList.add('active');

        // Focus first input for accessibility
        setTimeout(() => {
            const firstInput = modal.querySelector('input[type="radio"], textarea');
            if (firstInput) firstInput.focus();
        }, 100);
    },

    /**
     * Load existing feedback into modal form
     */
    async loadExistingFeedback(type, id) {
        try {
            const response = await apiFetch(`/engagement/${type}/${id}/my-feedback`);
            if (response.status === 'found' && response.feedback) {
                const { accuracy_rating, usefulness_rating, quality_rating, comment } = response.feedback;

                // Populate form fields based on type
                if (type === 'synthesis') {
                    this.setRatingValue('accuracy-rating', accuracy_rating);
                    this.setRatingValue('usefulness-rating', usefulness_rating);
                } else {
                    this.setRatingValue('quality-rating', quality_rating);
                }

                const commentField = document.getElementById('feedback-comment');
                if (commentField && comment) {
                    commentField.value = comment;
                }
            }
        } catch (error) {
            console.error('[Feedback] Error loading existing feedback:', error);
        }
    },

    /**
     * Set rating value in star input
     */
    setRatingValue(containerId, value) {
        if (!value) return;
        const container = document.getElementById(containerId);
        if (!container) return;
        const input = container.querySelector(`input[value="${value}"]`);
        if (input) input.checked = true;
    },

    /**
     * Submit detailed feedback from modal
     */
    async submitDetailedFeedback(e) {
        e.preventDefault();

        const modal = document.getElementById('feedback-modal');
        const type = modal.dataset.feedbackType;
        const id = parseInt(modal.dataset.feedbackId);

        const form = e.target;
        const formData = new FormData(form);

        let body;
        if (type === 'synthesis') {
            const accuracyRating = formData.get('accuracy_rating');
            const usefulnessRating = formData.get('usefulness_rating');

            if (!accuracyRating || !usefulnessRating) {
                if (typeof ToastManager !== 'undefined') {
                    ToastManager.warning('Please rate both accuracy and usefulness.', 'Missing Ratings');
                }
                return;
            }

            body = {
                accuracy_rating: parseInt(accuracyRating),
                usefulness_rating: parseInt(usefulnessRating),
                comment: formData.get('comment') || null
            };
        } else {
            const qualityRating = formData.get('quality_rating');

            if (!qualityRating) {
                if (typeof ToastManager !== 'undefined') {
                    ToastManager.warning('Please rate the quality.', 'Missing Rating');
                }
                return;
            }

            body = {
                quality_rating: parseInt(qualityRating),
                comment: formData.get('comment') || null
            };
        }

        const submitBtn = form.querySelector('[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.add('loading');
        }

        try {
            const response = await apiFetch(`/engagement/${type}/${id}/detailed`, {
                method: 'POST',
                body: JSON.stringify(body)
            });

            if (response.status === 'success') {
                // Close modal
                this.closeFeedbackModal();

                // Show toast
                if (typeof ToastManager !== 'undefined') {
                    ToastManager.success('Your detailed feedback has been recorded.', 'Thank You!');
                }

                // Announce to screen readers
                if (typeof AccessibilityManager !== 'undefined') {
                    AccessibilityManager.announce('Detailed feedback submitted successfully');
                }
            }
        } catch (error) {
            console.error('[Feedback] Error submitting detailed feedback:', error);
            if (typeof ToastManager !== 'undefined') {
                ToastManager.error('Failed to submit feedback. Please try again.', 'Error');
            }
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.classList.remove('loading');
            }
        }
    },

    /**
     * Close feedback modal
     */
    closeFeedbackModal() {
        const modal = document.getElementById('feedback-modal');
        if (modal) {
            modal.classList.remove('active');
        }
    },

    /**
     * Generate feedback buttons HTML for a synthesis
     * @param {number} synthesisId - The synthesis ID
     * @returns {string} HTML string for feedback buttons
     */
    renderSynthesisFeedbackButtons(synthesisId) {
        return `
            <div class="feedback-buttons" data-feedback-container="synthesis-${synthesisId}">
                <button class="btn btn-icon btn-ghost feedback-btn"
                        data-feedback-up
                        data-feedback-type="synthesis"
                        data-feedback-id="${synthesisId}"
                        aria-label="This was helpful"
                        aria-pressed="false"
                        title="Helpful">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                    </svg>
                </button>
                <button class="btn btn-icon btn-ghost feedback-btn"
                        data-feedback-down
                        data-feedback-type="synthesis"
                        data-feedback-id="${synthesisId}"
                        aria-label="This wasn't helpful"
                        aria-pressed="false"
                        title="Not Helpful">
                    <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                    </svg>
                </button>
                <button class="btn btn-ghost btn-sm feedback-btn-detailed"
                        data-feedback-detailed
                        data-feedback-type="synthesis"
                        data-feedback-id="${synthesisId}"
                        title="Give detailed feedback">
                    More feedback
                </button>
            </div>
        `;
    },

    /**
     * Generate feedback buttons HTML for a theme
     * @param {number} themeId - The theme ID
     * @returns {string} HTML string for feedback buttons
     */
    renderThemeFeedbackButtons(themeId) {
        return `
            <div class="feedback-buttons" data-feedback-container="theme-${themeId}">
                <button class="btn btn-icon btn-ghost feedback-btn feedback-btn-sm"
                        data-feedback-up
                        data-feedback-type="theme"
                        data-feedback-id="${themeId}"
                        aria-label="This theme is relevant"
                        aria-pressed="false"
                        title="Relevant">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                    </svg>
                </button>
                <button class="btn btn-icon btn-ghost feedback-btn feedback-btn-sm"
                        data-feedback-down
                        data-feedback-type="theme"
                        data-feedback-id="${themeId}"
                        aria-label="This theme is not relevant"
                        aria-pressed="false"
                        title="Not Relevant">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                    </svg>
                </button>
            </div>
        `;
    }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => FeedbackManager.init());
} else {
    FeedbackManager.init();
}

// Export for use in other modules
window.FeedbackManager = FeedbackManager;

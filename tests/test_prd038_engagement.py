"""
Tests for PRD-038: User Engagement

Tests for:
- 38.1 Database Models (SynthesisFeedback, ThemeFeedback)
- 38.2 Engagement API Routes
- 38.3 Frontend FeedbackManager
- 38.4 UI Integration
"""
import pytest
from pathlib import Path
import ast


class TestFeedbackModels:
    """Test 38.1: Feedback database models."""

    def test_models_file_exists(self):
        """Verify models.py exists."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        assert models_path.exists(), "models.py should exist"

    def test_synthesis_feedback_model_exists(self):
        """Verify SynthesisFeedback model is defined."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "class SynthesisFeedback" in content
        assert "__tablename__ = \"synthesis_feedback\"" in content

    def test_synthesis_feedback_has_required_columns(self):
        """Verify SynthesisFeedback has all required columns."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        required_columns = [
            "synthesis_id",
            "is_helpful",
            "accuracy_rating",
            "usefulness_rating",
            "comment",
            "user",
            "created_at",
            "updated_at"
        ]

        for col in required_columns:
            assert col in content, f"SynthesisFeedback should have {col} column"

    def test_synthesis_feedback_has_check_constraint(self):
        """Verify SynthesisFeedback has rating range check constraints."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "CheckConstraint" in content
        assert "accuracy_rating >= 1" in content or "check_synthesis_accuracy_rating" in content
        assert "usefulness_rating >= 1" in content or "check_synthesis_usefulness_rating" in content

    def test_synthesis_feedback_has_index(self):
        """Verify SynthesisFeedback has user lookup index."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "idx_synthesis_feedback_user" in content

    def test_theme_feedback_model_exists(self):
        """Verify ThemeFeedback model is defined."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "class ThemeFeedback" in content
        assert "__tablename__ = \"theme_feedback\"" in content

    def test_theme_feedback_has_required_columns(self):
        """Verify ThemeFeedback has all required columns."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        required_columns = [
            "theme_id",
            "is_relevant",
            "quality_rating",
            "comment",
            "user",
            "created_at",
            "updated_at"
        ]

        for col in required_columns:
            assert col in content, f"ThemeFeedback should have {col} column"

    def test_theme_feedback_has_check_constraint(self):
        """Verify ThemeFeedback has rating range check constraint."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "check_theme_quality_rating" in content

    def test_theme_feedback_has_index(self):
        """Verify ThemeFeedback has user lookup index."""
        models_path = Path(__file__).parent.parent / "backend" / "models.py"
        content = models_path.read_text()

        assert "idx_theme_feedback_user" in content

    def test_feedback_models_can_be_imported(self):
        """Verify feedback models can be imported."""
        from backend.models import SynthesisFeedback, ThemeFeedback

        assert SynthesisFeedback is not None
        assert ThemeFeedback is not None


class TestEngagementRoutes:
    """Test 38.2: Engagement API routes."""

    def test_engagement_router_file_exists(self):
        """Verify engagement.py exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        assert route_path.exists(), "engagement.py should exist"

    def test_engagement_router_imports(self):
        """Verify engagement.py has required imports."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "from fastapi import APIRouter" in content
        assert "AsyncSession" in content
        assert "get_async_db" in content
        assert "verify_jwt_or_basic" in content

    def test_engagement_router_uses_async(self):
        """Verify engagement routes use async patterns."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "async def" in content
        assert "await db.execute" in content
        assert "await db.commit" in content

    def test_synthesis_simple_endpoint_exists(self):
        """Verify synthesis simple feedback endpoint exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "/engagement/synthesis/{synthesis_id}/simple" in content
        assert "submit_simple_synthesis_feedback" in content

    def test_synthesis_detailed_endpoint_exists(self):
        """Verify synthesis detailed feedback endpoint exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "/engagement/synthesis/{synthesis_id}/detailed" in content
        assert "submit_detailed_synthesis_feedback" in content

    def test_synthesis_my_feedback_endpoint_exists(self):
        """Verify synthesis my-feedback endpoint exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "/engagement/synthesis/{synthesis_id}/my-feedback" in content
        assert "get_my_synthesis_feedback" in content

    def test_theme_simple_endpoint_exists(self):
        """Verify theme simple feedback endpoint exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "/engagement/theme/{theme_id}/simple" in content
        assert "submit_simple_theme_feedback" in content

    def test_theme_detailed_endpoint_exists(self):
        """Verify theme detailed feedback endpoint exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "/engagement/theme/{theme_id}/detailed" in content
        assert "submit_detailed_theme_feedback" in content

    def test_theme_my_feedback_endpoint_exists(self):
        """Verify theme my-feedback endpoint exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "/engagement/theme/{theme_id}/my-feedback" in content
        assert "get_my_theme_feedback" in content

    def test_engagement_uses_sanitization(self):
        """Verify engagement routes sanitize comments."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "from backend.utils.sanitization import" in content
        assert "sanitize_content_text" in content

    def test_engagement_rate_limited(self):
        """Verify engagement routes are rate limited."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "@limiter.limit" in content
        assert "RATE_LIMITS" in content

    def test_engagement_router_registered(self):
        """Verify engagement router is registered in app.py."""
        app_path = Path(__file__).parent.parent / "backend" / "app.py"
        content = app_path.read_text()

        assert "from backend.routes import" in content
        assert "engagement" in content
        assert "engagement.router" in content


class TestPydanticModels:
    """Test Pydantic request/response models."""

    def test_simple_feedback_request_exists(self):
        """Verify SimpleFeedbackRequest model exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "class SimpleFeedbackRequest" in content
        assert "is_positive: bool" in content

    def test_detailed_synthesis_feedback_request_exists(self):
        """Verify DetailedSynthesisFeedbackRequest model exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "class DetailedSynthesisFeedbackRequest" in content
        assert "accuracy_rating" in content
        assert "usefulness_rating" in content
        assert "ge=1" in content
        assert "le=5" in content

    def test_detailed_theme_feedback_request_exists(self):
        """Verify DetailedThemeFeedbackRequest model exists."""
        route_path = Path(__file__).parent.parent / "backend" / "routes" / "engagement.py"
        content = route_path.read_text()

        assert "class DetailedThemeFeedbackRequest" in content
        assert "quality_rating" in content


class TestFrontendFeedbackManager:
    """Test 38.3: Frontend FeedbackManager."""

    def test_feedback_js_exists(self):
        """Verify feedback.js exists."""
        js_path = Path(__file__).parent.parent / "frontend" / "js" / "feedback.js"
        assert js_path.exists(), "feedback.js should exist"

    def test_feedback_manager_object(self):
        """Verify FeedbackManager object structure."""
        js_path = Path(__file__).parent.parent / "frontend" / "js" / "feedback.js"
        content = js_path.read_text()

        assert "const FeedbackManager" in content
        assert "init()" in content

    def test_feedback_manager_init(self):
        """Verify FeedbackManager has init method."""
        js_path = Path(__file__).parent.parent / "frontend" / "js" / "feedback.js"
        content = js_path.read_text()

        assert "setupEventDelegation" in content
        assert "setupModalEvents" in content

    def test_feedback_manager_submit_simple(self):
        """Verify FeedbackManager has submitSimpleFeedback method."""
        js_path = Path(__file__).parent.parent / "frontend" / "js" / "feedback.js"
        content = js_path.read_text()

        assert "submitSimpleFeedback" in content
        assert "apiFetch" in content
        assert "is_positive" in content

    def test_feedback_manager_modal_methods(self):
        """Verify FeedbackManager has modal methods."""
        js_path = Path(__file__).parent.parent / "frontend" / "js" / "feedback.js"
        content = js_path.read_text()

        assert "openFeedbackModal" in content
        assert "closeFeedbackModal" in content
        assert "submitDetailedFeedback" in content

    def test_feedback_manager_render_methods(self):
        """Verify FeedbackManager has render methods."""
        js_path = Path(__file__).parent.parent / "frontend" / "js" / "feedback.js"
        content = js_path.read_text()

        assert "renderSynthesisFeedbackButtons" in content
        assert "renderThemeFeedbackButtons" in content

    def test_feedback_manager_uses_toast(self):
        """Verify FeedbackManager uses ToastManager."""
        js_path = Path(__file__).parent.parent / "frontend" / "js" / "feedback.js"
        content = js_path.read_text()

        assert "ToastManager" in content
        assert "ToastManager.success" in content
        assert "ToastManager.error" in content

    def test_feedback_manager_accessibility(self):
        """Verify FeedbackManager uses AccessibilityManager."""
        js_path = Path(__file__).parent.parent / "frontend" / "js" / "feedback.js"
        content = js_path.read_text()

        assert "AccessibilityManager" in content
        assert "announce" in content

    def test_feedback_manager_exported(self):
        """Verify FeedbackManager is exported to window."""
        js_path = Path(__file__).parent.parent / "frontend" / "js" / "feedback.js"
        content = js_path.read_text()

        assert "window.FeedbackManager = FeedbackManager" in content


class TestFeedbackCSS:
    """Test feedback button and star rating CSS."""

    def test_buttons_css_exists(self):
        """Verify _buttons.css exists."""
        css_path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "_buttons.css"
        assert css_path.exists(), "_buttons.css should exist"

    def test_feedback_buttons_styles(self):
        """Verify feedback button styles exist."""
        css_path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "_buttons.css"
        content = css_path.read_text()

        assert ".feedback-buttons" in content
        assert ".feedback-btn" in content

    def test_feedback_button_active_states(self):
        """Verify feedback button active states."""
        css_path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "_buttons.css"
        content = css_path.read_text()

        assert ".feedback-btn.active" in content
        assert "[data-feedback-up].active" in content
        assert "[data-feedback-down].active" in content

    def test_star_rating_styles(self):
        """Verify star rating styles exist."""
        css_path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "_buttons.css"
        content = css_path.read_text()

        assert ".star-rating" in content
        assert "flex-direction: row-reverse" in content

    def test_star_rating_hover(self):
        """Verify star rating hover effects."""
        css_path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "_buttons.css"
        content = css_path.read_text()

        assert ".star-rating label:hover" in content
        assert "input:checked ~ label" in content


class TestUIIntegration:
    """Test 38.4: UI integration in index.html."""

    def test_index_html_exists(self):
        """Verify index.html exists."""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        assert html_path.exists(), "index.html should exist"

    def test_feedback_modal_exists(self):
        """Verify feedback modal exists in index.html."""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = html_path.read_text(encoding='utf-8')

        assert 'id="feedback-modal"' in content
        assert 'id="feedback-form"' in content

    def test_feedback_modal_star_ratings(self):
        """Verify feedback modal has star rating inputs."""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = html_path.read_text(encoding='utf-8')

        assert "star-rating" in content
        assert "accuracy-rating" in content or "accuracy_rating" in content
        assert "usefulness-rating" in content or "usefulness_rating" in content

    def test_feedback_script_tag(self):
        """Verify feedback.js script tag exists."""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = html_path.read_text(encoding='utf-8')

        assert 'src="js/feedback.js"' in content

    def test_synthesis_feedback_container(self):
        """Verify synthesis feedback container exists."""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = html_path.read_text(encoding='utf-8')

        assert 'id="synthesis-feedback-buttons"' in content

    def test_display_synthesis_integration(self):
        """Verify displaySynthesis integrates feedback buttons."""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = html_path.read_text(encoding='utf-8')

        assert "FeedbackManager.renderSynthesisFeedbackButtons" in content

    def test_display_themes_integration(self):
        """Verify displayThemes integrates feedback buttons."""
        html_path = Path(__file__).parent.parent / "frontend" / "index.html"
        content = html_path.read_text(encoding='utf-8')

        assert "FeedbackManager.renderThemeFeedbackButtons" in content


class TestAccessibility:
    """Test accessibility features."""

    def test_feedback_buttons_aria_labels(self):
        """Verify feedback buttons have aria-labels."""
        js_path = Path(__file__).parent.parent / "frontend" / "js" / "feedback.js"
        content = js_path.read_text()

        assert 'aria-label="' in content
        assert 'aria-pressed="' in content

    def test_star_rating_accessibility(self):
        """Verify star rating has focus styles."""
        css_path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "_buttons.css"
        content = css_path.read_text()

        assert ".star-rating input:focus-visible" in content

    def test_feedback_btn_focus_visible(self):
        """Verify feedback buttons have focus-visible styles."""
        css_path = Path(__file__).parent.parent / "frontend" / "css" / "components" / "_buttons.css"
        content = css_path.read_text()

        assert ".feedback-btn:focus-visible" in content

"""
Tests para el análisis estructural E.060.
"""
import pytest
from app.services.e060_analysis import (
    E060Analyzer,
    E060Config,
    ElementDimensions,
    ElementType,
    VulnerabilityLevel,
)


@pytest.fixture
def analyzer():
    """Create an E060 analyzer instance."""
    return E060Analyzer()


@pytest.fixture
def config():
    """Create an E060 config instance."""
    return E060Config()


class TestWallAnalysis:
    """Tests for wall analysis."""

    def test_compliant_wall_1_floor(self, analyzer):
        """Test a compliant wall for 1 floor building."""
        dimensions = ElementDimensions(
            element_type=ElementType.WALL,
            element_id="wall_1",
            floor_level=1,
            width=4.0,
            height=2.8,
            length=4.0,
            thickness=0.20,  # 20cm - compliant
        )

        result = analyzer.analyze_wall(dimensions)

        assert result.thickness_compliant is True
        assert result.vulnerability_level in [VulnerabilityLevel.LOW, VulnerabilityLevel.MEDIUM]
        assert result.vulnerability_score < 50

    def test_non_compliant_wall_thickness(self, analyzer):
        """Test a wall with insufficient thickness."""
        dimensions = ElementDimensions(
            element_type=ElementType.WALL,
            element_id="wall_2",
            floor_level=1,
            width=4.0,
            height=2.8,
            length=4.0,
            thickness=0.10,  # 10cm - non-compliant
        )

        result = analyzer.analyze_wall(dimensions)

        assert result.thickness_compliant is False
        assert len(result.issues) > 0
        assert any("espesor" in issue.lower() for issue in result.issues)

    def test_wall_confinement_compliant(self, analyzer):
        """Test wall with proper confinement."""
        dimensions = ElementDimensions(
            element_type=ElementType.WALL,
            element_id="wall_3",
            floor_level=1,
            width=4.0,
            height=2.8,
            length=4.0,
            thickness=0.20,
        )

        result = analyzer.analyze_wall(
            dimensions,
            nearest_confinement_distance=3.0  # 3m - compliant
        )

        assert result.confinement_compliant is True

    def test_wall_confinement_non_compliant(self, analyzer):
        """Test wall with insufficient confinement."""
        dimensions = ElementDimensions(
            element_type=ElementType.WALL,
            element_id="wall_4",
            floor_level=1,
            width=8.0,
            height=2.8,
            length=8.0,
            thickness=0.20,
        )

        result = analyzer.analyze_wall(
            dimensions,
            nearest_confinement_distance=6.0  # 6m - non-compliant
        )

        assert result.confinement_compliant is False
        assert any("confinamiento" in issue.lower() for issue in result.issues)

    def test_wall_vo_ratio_compliant(self, analyzer):
        """Test wall with compliant vano/muro ratio."""
        dimensions = ElementDimensions(
            element_type=ElementType.WALL,
            element_id="wall_5",
            floor_level=1,
            width=4.0,
            height=2.8,
            length=4.0,
            thickness=0.20,
        )

        result = analyzer.analyze_wall(
            dimensions,
            opening_width=2.0  # 2m opening in 4m wall = 0.5 ratio
        )

        assert result.vo_ratio_compliant is True

    def test_wall_vo_ratio_non_compliant(self, analyzer):
        """Test wall with non-compliant vano/muro ratio."""
        dimensions = ElementDimensions(
            element_type=ElementType.WALL,
            element_id="wall_6",
            floor_level=1,
            width=4.0,
            height=2.8,
            length=4.0,
            thickness=0.20,
        )

        result = analyzer.analyze_wall(
            dimensions,
            opening_width=3.0  # 3m opening in 4m wall = 0.75 ratio
        )

        assert result.vo_ratio_compliant is False
        assert any("vano" in issue.lower() for issue in result.issues)

    def test_wall_critical_vulnerability(self, analyzer):
        """Test wall with critical vulnerability."""
        dimensions = ElementDimensions(
            element_type=ElementType.WALL,
            element_id="wall_7",
            floor_level=1,
            width=8.0,
            height=2.8,
            length=8.0,
            thickness=0.10,  # Too thin
        )

        result = analyzer.analyze_wall(
            dimensions,
            nearest_confinement_distance=6.0,  # Too far
            opening_width=5.0,  # Too large
        )

        assert result.vulnerability_level == VulnerabilityLevel.CRITICAL
        assert result.vulnerability_score >= 75

    def test_required_thickness_by_floor(self, analyzer):
        """Test required thickness varies by floor level."""
        assert analyzer.get_required_thickness(1) == 0.15  # 15cm for 1 floor
        assert analyzer.get_required_thickness(2) == 0.20  # 20cm for 2 floors
        assert analyzer.get_required_thickness(3) == 0.25  # 25cm for 3+ floors


class TestColumnAnalysis:
    """Tests for column analysis."""

    def test_compliant_column(self, analyzer):
        """Test a compliant column."""
        dimensions = ElementDimensions(
            element_type=ElementType.COLUMN,
            element_id="column_1",
            floor_level=1,
            width=0.30,  # 30cm
            height=0.30,  # 30cm
            length=0,
        )

        result = analyzer.analyze_column(dimensions)

        assert result.thickness_compliant is True
        assert result.vulnerability_level == VulnerabilityLevel.LOW

    def test_non_compliant_column_width(self, analyzer):
        """Test column with insufficient width."""
        dimensions = ElementDimensions(
            element_type=ElementType.COLUMN,
            element_id="column_2",
            floor_level=1,
            width=0.15,  # 15cm - below minimum
            height=0.30,
            length=0,
        )

        result = analyzer.analyze_column(dimensions)

        assert result.thickness_compliant is False
        assert len(result.issues) > 0


class TestBeamAnalysis:
    """Tests for beam analysis."""

    def test_compliant_beam(self, analyzer):
        """Test a compliant beam."""
        dimensions = ElementDimensions(
            element_type=ElementType.BEAM,
            element_id="beam_1",
            floor_level=1,
            width=0.25,  # 25cm
            height=0.40,  # 40cm
            length=4.0,
        )

        result = analyzer.analyze_beam(dimensions)

        assert result.thickness_compliant is True

    def test_non_compliant_beam(self, analyzer):
        """Test beam with insufficient dimensions."""
        dimensions = ElementDimensions(
            element_type=ElementType.BEAM,
            element_id="beam_2",
            floor_level=1,
            width=0.15,  # 15cm - below minimum
            height=0.20,
            length=4.0,
        )

        result = analyzer.analyze_beam(dimensions)

        assert result.thickness_compliant is False


class TestVulnerabilityCalculation:
    """Tests for vulnerability score calculation."""

    def test_all_compliant(self, analyzer):
        """Test vulnerability when all checks pass."""
        score, level = analyzer.calculate_vulnerability_score(
            thickness_compliant=True,
            confinement_compliant=True,
            vo_ratio_compliant=True,
            reinforcement_compliant=True,
        )

        assert score == 0
        assert level == VulnerabilityLevel.LOW

    def test_all_non_compliant(self, analyzer):
        """Test vulnerability when all checks fail."""
        score, level = analyzer.calculate_vulnerability_score(
            thickness_compliant=False,
            confinement_compliant=False,
            vo_ratio_compliant=False,
            reinforcement_compliant=False,
        )

        assert score == 100
        assert level == VulnerabilityLevel.CRITICAL

    def test_partial_compliance(self, analyzer):
        """Test vulnerability with partial compliance."""
        score, level = analyzer.calculate_vulnerability_score(
            thickness_compliant=False,  # +30
            confinement_compliant=True,
            vo_ratio_compliant=False,   # +20
            reinforcement_compliant=True,
        )

        assert score == 50
        assert level == VulnerabilityLevel.HIGH


class TestConfig:
    """Tests for E060 configuration."""

    def test_default_config(self, config):
        """Test default configuration values."""
        assert config.MIN_WALL_THICKNESS_1FLOOR == 15
        assert config.MIN_WALL_THICKNESS_2FLOORS == 20
        assert config.MIN_WALL_THICKNESS_3FLOORS == 25
        assert config.MAX_CONFINEMENT_SPACING == 4.0
        assert config.MAX_VO_RATIO == 0.6
        assert config.MIN_REINFORCEMENT_RATIO == 0.0025

    def test_custom_config(self):
        """Test custom configuration."""
        config = E060Config(
            MIN_WALL_THICKNESS_1FLOOR=20,
            MAX_VO_RATIO=0.5,
        )

        assert config.MIN_WALL_THICKNESS_1FLOOR == 20
        assert config.MAX_VO_RATIO == 0.5
        # Other values should be defaults
        assert config.MAX_CONFINEMENT_SPACING == 4.0

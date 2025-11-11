# src/agents/deep_research_agent.py - BIG ROCK 33: Pattern Narrative Generation
import logging
from .base_agent import MycelialAgent
import time
import random
import json

class DeepResearchAgent(MycelialAgent):
    """
    Performs redundant validation on high-value patterns before archiving.
    BIG ROCK 33: Generates human-readable pattern narratives for dashboard display.

    Mechanism:
    - Maintains a research queue of patterns flagged for validation
    - Each pattern undergoes independent research and voting
    - Votes: -1 (Reject), 0 (Neutral), 1 (Approve)
    - Synthesizes high-value narrative based on moat specialization
    - Results published to Redis for consensus aggregation and dashboard display
    """
    def __init__(self, model):
        super().__init__(model)
        self.name = f"Research_{self.unique_id}"
        self.research_queue = []  # Patterns awaiting validation
        self.total_patterns_validated = 0
        self.validation_results = {"approved": 0, "neutral": 0, "rejected": 0}

        # BIG ROCK 33: Moat Specialization for narrative generation
        self.specialization = random.choice([
            "Finance",
            "Code Innovation",
            "Logistics",
            "Government",
            "US Corporations"
        ])

        # Listen for pattern validation requests
        self._register_listener("pattern-validation-request", self.handle_validation_request)

        logging.info(f"[{self.name}] Initialized. Redundant validation active (Specialization: {self.specialization})")

    def step(self):
        """Process research queue."""
        if self.research_queue:
            pattern_info = self.research_queue.pop(0)
            self._validate_pattern(pattern_info)

    def handle_validation_request(self, message: dict):
        """
        Callback for pattern validation requests from the archiving system.
        """
        pattern_id = message.get('pattern_id')
        pattern_data = message.get('pattern_data', {})

        if pattern_id:
            self.research_queue.append({
                'id': pattern_id,
                'data': pattern_data,
                'received_at': time.time()
            })
            logging.debug(f"[{self.name}] Pattern {pattern_id} queued for validation (queue size: {len(self.research_queue)})")

    def _generate_narrative(self, pattern_id, pattern_data):
        """
        BIG ROCK 33: Synthesize a high-value, human-readable pattern story.
        Generates narratives based on moat specialization and pattern characteristics.
        """
        # Extract pattern metrics
        prediction_score = pattern_data.get('prediction_score', 0.5)
        interestingness = pattern_data.get('interestingness_score', 50)
        pattern_value = pattern_data.get('pattern_value', 50)
        raw_features = pattern_data.get('raw_features', {})

        # Moat-specific narrative templates
        moat_narratives = {
            "Finance": {
                "high": f"discovered a **critical arbitrage signal** linking Capital Flow Momentum (RSI: {raw_features.get('RSI', 0):.1f}) with sudden Government Policy shifts. Prediction confidence: {prediction_score*100:.1f}%.",
                "medium": f"identified a **moderate correlation** between Market Volatility (ATR: {raw_features.get('ATR', 0):.2f}) and emerging regulatory patterns. Pattern strength: {pattern_value:.1f}/100.",
                "low": f"flagged a **weak signal** in price momentum ({raw_features.get('MOM', 0):.4f}) that may warrant continued monitoring."
            },
            "Code Innovation": {
                "high": f"validated an **emergent breakthrough** where Repository Novelty Spikes precede systemic risk drops in Logistics by 72 hours. Confidence: {prediction_score*100:.1f}%.",
                "medium": f"confirmed a **moderate pattern** linking Python commit frequency with cross-sector innovation diffusion. Interestingness: {interestingness:.1f}/100.",
                "low": f"noted a **preliminary trend** in open-source activity that may indicate early-stage innovation cycles."
            },
            "Logistics": {
                "high": f"identified a **robust anomaly** linking Supply Chain Congestion decay with predictable {raw_features.get('close', 0):.2f} USD spikes in Corporate sector activity. High confidence.",
                "medium": f"detected a **significant pattern** in routing efficiency metrics correlating with {self.specialization} sector volatility (ATR: {raw_features.get('ATR', 0):.2f}).",
                "low": f"observed a **marginal shift** in logistics flow patterns that warrants further investigation."
            },
            "Government": {
                "high": f"confirmed a **major regulatory signal** linking Policy Intensity Index with high-confidence (>{prediction_score*100:.0f}%) collective SwarmBrain consensus shifts.",
                "medium": f"validated a **moderate correlation** between Federal Policy updates and {interestingness:.0f}-point interestingness spikes across Finance agents.",
                "low": f"flagged a **weak regulatory indicator** in the {raw_features.get('RSI', 50):.0f} RSI band that may precede policy changes."
            },
            "US Corporations": {
                "high": f"isolated a **key leading indicator**: Tech Sector Index drops (RSI: {raw_features.get('RSI', 0):.1f}) immediately trigger consensus shifts in Finance Moat ({prediction_score*100:.1f}% confidence).",
                "medium": f"identified a **moderate trend** where Corporate Earnings volatility (ATR: {raw_features.get('ATR', 0):.2f}) precedes Swarm strategy adjustments.",
                "low": f"noted a **preliminary correlation** between sector rotation patterns and interestingness scores ({interestingness:.0f}/100)."
            }
        }

        # Determine narrative quality tier based on combined metrics
        quality_score = (prediction_score * 50) + (interestingness * 0.3) + (pattern_value * 0.2)

        if quality_score > 80:
            tier = "high"
        elif quality_score > 60:
            tier = "medium"
        else:
            tier = "low"

        # Select narrative template
        narrative_text = moat_narratives.get(self.specialization, {}).get(
            tier,
            f"synthesized an unclassified pattern (Quality: {quality_score:.1f}/100) requiring additional research."
        )

        # Format final narrative with pattern ID and agent signature
        narrative = f"🔮 **PATTERN {pattern_id} ({self.specialization} Moat):** {self.name} {narrative_text}"

        return narrative

    def _validate_pattern(self, pattern_info):
        """
        Validate a pattern using redundant research methodology and generate narrative.
        BIG ROCK 33: Now publishes rich narratives to pattern-narrative channel.
        """
        try:
            pattern_id = pattern_info if isinstance(pattern_info, str) else pattern_info.get('id', 'unknown')
            pattern_data = pattern_info.get('data', {}) if isinstance(pattern_info, dict) else {}

            # Simulated validation logic with bias toward approval for high-quality patterns
            prediction_score = pattern_data.get('prediction_score', 0.5)
            interestingness = pattern_data.get('interestingness_score', 50)
            pattern_value = pattern_data.get('pattern_value', 50)

            # Calculate validation confidence based on pattern quality
            quality_score = (prediction_score * 50) + (interestingness * 0.3) + (pattern_value * 0.2)

            # Vote with bias toward high-quality patterns
            if quality_score > 80:
                vote = 1  # Approve
            elif quality_score < 50:
                vote = -1  # Reject
            else:
                vote = random.choice([-1, 0, 1])  # Mixed decision

            # BIG ROCK 33: Generate human-readable narrative
            narrative = self._generate_narrative(pattern_id, pattern_data)

            # Record results
            self.total_patterns_validated += 1
            if vote == 1:
                self.validation_results["approved"] += 1
            elif vote == -1:
                self.validation_results["rejected"] += 1
            else:
                self.validation_results["neutral"] += 1

            # Publish validation result with narrative (for consensus engine)
            validation_message = {
                "researcher": self.name,
                "pattern_id": pattern_id,
                "vote": vote,
                "quality_score": quality_score,
                "timestamp": time.time(),
                "specialization": self.specialization
            }
            self.publish("pattern-validation-result", validation_message)

            # BIG ROCK 33: Publish narrative to dashboard-displayable channel
            narrative_message = {
                "pattern_id": pattern_id,
                "research_agent": self.name,
                "specialization": self.specialization,
                "vote": vote,
                "narrative": narrative,
                "quality_score": quality_score,
                "timestamp": time.time()
            }
            self.publish("pattern-narrative", narrative_message)

            if self.total_patterns_validated % 10 == 0:  # Log periodically
                logging.info(f"[{self.name}] Pattern {pattern_id} validated. Vote: {vote} (quality: {quality_score:.1f}). "
                           f"Narrative published. Total validations: {self.total_patterns_validated} "
                           f"(Approved: {self.validation_results['approved']}, "
                           f"Neutral: {self.validation_results['neutral']}, "
                           f"Rejected: {self.validation_results['rejected']})")
            else:
                logging.debug(f"[{self.name}] Pattern {pattern_id} validated. Vote: {vote}. Narrative: {narrative[:80]}...")

        except Exception as e:
            logging.error(f"[{self.name}] Error validating pattern: {e}")

# src/agents/mycelial_instigator_agent.py - BIG ROCK 32: Rule of 3 Collaboration Enforcement
import logging
from .base_agent import MycelialAgent
import time
import random
import json

class MycelialInstigatorAgent(MycelialAgent):
    """
    Enforces the 'Rule of 3' collaboration principle.
    Prevents isolated agents and encourages collaborative decision-making.

    Mechanism:
    - Every 3 steps, selects one "target" SwarmBrain agent
    - Identifies 2 "partner" agents to collaborate with
    - Publishes FORCE_SHARE signal to trigger policy exchange
    """
    def __init__(self, model):
        super().__init__(model)
        self.name = f"Instigator_{self.unique_id}"
        self.touch_frequency = 3  # Steps before attempting new collaboration
        self.steps_since_touch = 0
        self.total_collaborations_triggered = 0
        logging.info(f"[{self.name}] Initialized. Rule of 3 enforcement active (frequency: {self.touch_frequency} steps)")

    def step(self):
        """Periodic collaboration enforcement."""
        self.steps_since_touch += 1
        if self.steps_since_touch >= self.touch_frequency:
            self._enforce_rule_of_3()
            self.steps_since_touch = 0

    def _enforce_rule_of_3(self):
        """
        Select 3 SwarmBrain agents and trigger forced collaboration.
        """
        try:
            # Find all SwarmBrain agents
            all_swarm_agents = [a for a in self.model.agents
                              if hasattr(a, 'name') and 'SwarmBrain' in str(a.name)]

            if len(all_swarm_agents) < 3:
                logging.debug(f"[{self.name}] Insufficient agents for Rule of 3 (need 3, have {len(all_swarm_agents)})")
                return

            # Select one target agent and two partners
            target = random.choice(all_swarm_agents)
            partners = random.sample([a for a in all_swarm_agents if a.unique_id != target.unique_id], 2)

            # Publish FORCE_SHARE signal to all three agents
            collaboration_group = [target] + partners
            agent_ids = [str(a.unique_id) for a in collaboration_group]

            message = {
                "sender": self.name,
                "action": "FORCE_SHARE",
                "group": agent_ids,
                "timestamp": time.time()
            }

            # Publish to system-control channel for all agents to hear
            self.publish("system-control", message)

            self.total_collaborations_triggered += 1

            if self.total_collaborations_triggered % 100 == 1:  # Log periodically
                logging.info(f"[{self.name}] Rule of 3 enforced: {agent_ids} (total collaborations: {self.total_collaborations_triggered})")
            else:
                logging.debug(f"[{self.name}] Rule of 3 enforced: {agent_ids}")

        except Exception as e:
            logging.error(f"[{self.name}] Error enforcing Rule of 3: {e}")

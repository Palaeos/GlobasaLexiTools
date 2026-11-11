from .tense import TenseParticleRule
from .negation import NegationRule
from .np_structure import NPStructureRule
from .question import QuestionRule
from .conditional import ConditionalRule
from .passive import PassiveAgentRule
from .adverb_mo import AdverbMoRule
from .noun_pile import NounPileRule
from .noun_as_verb import NounAsVerbRule

ALL_RULES = [TenseParticleRule, NegationRule, NPStructureRule, QuestionRule,
             ConditionalRule, PassiveAgentRule, AdverbMoRule, NounPileRule,
             NounAsVerbRule]

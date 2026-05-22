#!/usr/bin/env python3
"""
Deriv Bot - Match/Differ Prediction (0-9)
Predicts whether the next digit will match or differ from the current digit
Uses historical data analysis and pattern recognition
"""

import json
import time
from collections import deque
from typing import Dict, List, Tuple, Optional


class DerivBotMatchDiffer:
    """
    A bot for predicting Match/Differ outcomes in Deriv trading
    Analyzes digit patterns and predicts if next digit matches current or differs
    """
    
    def __init__(self, max_history: int = 100, min_confidence: float = 0.55):
        """
        Initialize the Deriv bot
        
        Args:
            max_history: Maximum number of historical values to keep
            min_confidence: Minimum confidence level to place a trade (0.0-1.0)
        """
        self.max_history = max_history
        self.min_confidence = min_confidence
        self.digit_history: deque = deque(maxlen=max_history)
        self.predictions: List[Dict] = []
        self.trades: List[Dict] = []
        self.statistics = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'match_count': 0,
            'differ_count': 0,
            'win_rate': 0.0,
            'profit_loss': 0.0
        }
    
    def add_digit(self, digit: int) -> None:
        """
        Add a new digit to the history
        
        Args:
            digit: Digit value (0-9)
        """
        if not isinstance(digit, int) or digit < 0 or digit > 9:
            raise ValueError("Digit must be an integer between 0-9")
        self.digit_history.append(digit)
    
    def analyze_patterns(self) -> Dict:
        """
        Analyze historical patterns for match/differ occurrences
        
        Returns:
            Dictionary containing pattern statistics
        """
        if len(self.digit_history) < 2:
            return {}
        
        history = list(self.digit_history)
        matches = sum(1 for i in range(len(history) - 1) 
                     if history[i] == history[i + 1])
        differs = len(history) - 1 - matches
        
        total = matches + differs
        match_ratio = matches / total if total > 0 else 0.5
        differ_ratio = differs / total if total > 0 else 0.5
        
        return {
            'total_comparisons': total,
            'matches': matches,
            'differs': differs,
            'match_ratio': match_ratio,
            'differ_ratio': differ_ratio
        }
    
    def get_digit_frequency(self) -> Dict[int, float]:
        """
        Calculate digit frequency in history
        
        Returns:
            Dictionary with digit frequencies
        """
        if not self.digit_history:
            return {}
        
        total = len(self.digit_history)
        frequency = {}
        
        for digit in range(10):
            count = self.digit_history.count(digit)
            frequency[digit] = count / total if total > 0 else 0
        
        return frequency
    
    def predict_next(self, current_digit: int) -> Dict:
        """
        Predict whether next digit will match or differ from current
        
        Args:
            current_digit: Current digit (0-9)
            
        Returns:
            Prediction dictionary with confidence scores
        """
        if not isinstance(current_digit, int) or current_digit < 0 or current_digit > 9:
            raise ValueError("Current digit must be between 0-9")
        
        patterns = self.analyze_patterns()
        
        if not patterns:
            # Default prediction if insufficient history
            return {
                'prediction': 'differ',
                'match_confidence': 0.5,
                'differ_confidence': 0.5,
                'recommended_bet': None,
                'reason': 'Insufficient historical data'
            }
        
        match_ratio = patterns['match_ratio']
        differ_ratio = patterns['differ_ratio']
        
        # Adjust confidence based on digit frequency
        digit_freq = self.get_digit_frequency()
        current_freq = digit_freq.get(current_digit, 0)
        
        # Higher frequency of current digit increases match likelihood
        match_adjustment = current_freq * 0.3
        match_confidence = match_ratio + match_adjustment
        
        differ_confidence = 1.0 - match_confidence
        
        # Ensure values are valid probabilities
        match_confidence = min(max(match_confidence, 0.0), 1.0)
        differ_confidence = min(max(differ_confidence, 0.0), 1.0)
        
        # Determine prediction based on higher confidence
        if match_confidence > differ_confidence:
            prediction = 'match'
            confidence = match_confidence
        else:
            prediction = 'differ'
            confidence = differ_confidence
        
        recommended_bet = prediction if confidence >= self.min_confidence else None
        
        result = {
            'prediction': prediction,
            'match_confidence': round(match_confidence, 4),
            'differ_confidence': round(differ_confidence, 4),
            'recommended_bet': recommended_bet,
            'confidence_level': round(confidence, 4),
            'reason': self._get_prediction_reason(
                current_digit, patterns, digit_freq, prediction, confidence
            )
        }
        
        self.predictions.append(result)
        return result
    
    def _get_prediction_reason(self, current_digit: int, patterns: Dict, 
                               digit_freq: Dict, prediction: str, 
                               confidence: float) -> str:
        """Generate a reason for the prediction"""
        reasons = []
        
        if prediction == 'match':
            reasons.append(f"Digit {current_digit} has {digit_freq[current_digit]:.1%} frequency")
            reasons.append(f"Historical match rate: {patterns['match_ratio']:.1%}")
        else:
            reasons.append(f"Differ pattern observed in {patterns['differ_ratio']:.1%} of cases")
            reasons.append(f"Digit rotation likely")
        
        return " | ".join(reasons)
    
    def place_trade(self, bet_type: str, amount: float, 
                   outcome: Optional[str] = None) -> Dict:
        """
        Place a trade with prediction
        
        Args:
            bet_type: 'match' or 'differ'
            amount: Bet amount
            outcome: Actual outcome ('match' or 'differ') - for backtesting
            
        Returns:
            Trade dictionary with result
        """
        if bet_type not in ['match', 'differ']:
            raise ValueError("Bet type must be 'match' or 'differ'")
        
        trade = {
            'timestamp': time.time(),
            'bet_type': bet_type,
            'amount': amount,
            'outcome': outcome,
            'won': bet_type == outcome if outcome else None,
            'payout': amount * 2 if bet_type == outcome and outcome else -amount
        }
        
        self.trades.append(trade)
        
        if outcome:
            self.statistics['total_predictions'] += 1
            if trade['won']:
                self.statistics['correct_predictions'] += 1
                self.statistics['profit_loss'] += trade['payout']
            else:
                self.statistics['profit_loss'] -= amount
            
            if self.statistics['total_predictions'] > 0:
                self.statistics['win_rate'] = (
                    self.statistics['correct_predictions'] / 
                    self.statistics['total_predictions']
                )
        
        return trade
    
    def get_statistics(self) -> Dict:
        """Get bot statistics"""
        return {
            **self.statistics,
            'win_rate': f"{self.statistics['win_rate']:.2%}",
            'total_trades': len(self.trades),
            'history_size': len(self.digit_history)
        }
    
    def get_current_state(self) -> Dict:
        """Get current state of the bot"""
        return {
            'history': list(self.digit_history),
            'history_size': len(self.digit_history),
            'patterns': self.analyze_patterns(),
            'digit_frequency': self.get_digit_frequency(),
            'statistics': self.get_statistics(),
            'recent_predictions': self.predictions[-5:] if self.predictions else []
        }


def example_usage():
    """Example usage of the Deriv bot"""
    
    print("=" * 60)
    print("Deriv Bot - Match/Differ Prediction Example")
    print("=" * 60)
    
    # Initialize bot
    bot = DerivBotMatchDiffer(max_history=50, min_confidence=0.55)
    
    # Simulate digit stream
    digit_stream = [3, 3, 5, 7, 7, 7, 2, 2, 4, 6, 8, 8, 1, 3, 3, 5, 5, 9, 9, 0]
    
    print("\n1. Adding historical data...")
    for digit in digit_stream:
        bot.add_digit(digit)
    
    print(f"   Added {len(digit_stream)} digits to history")
    print(f"   Digit stream: {digit_stream}")
    
    # Analyze patterns
    print("\n2. Pattern Analysis:")
    patterns = bot.analyze_patterns()
    for key, value in patterns.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.2%}")
        else:
            print(f"   {key}: {value}")
    
    # Get frequency
    print("\n3. Digit Frequency:")
    freq = bot.get_digit_frequency()
    for digit, frequency in sorted(freq.items()):
        if frequency > 0:
            print(f"   Digit {digit}: {frequency:.2%}")
    
    # Make predictions
    print("\n4. Predictions for next digits:")
    test_digits = [0, 5, 9, 3]
    
    for current_digit in test_digits:
        prediction = bot.predict_next(current_digit)
        print(f"\n   Current Digit: {current_digit}")
        print(f"   Prediction: {prediction['prediction'].upper()}")
        print(f"   Match Confidence: {prediction['match_confidence']:.2%}")
        print(f"   Differ Confidence: {prediction['differ_confidence']:.2%}")
        print(f"   Recommended Bet: {prediction['recommended_bet']}")
        print(f"   Reason: {prediction['reason']}")
    
    # Simulate trades
    print("\n5. Simulating trades:")
    outcomes = ['match', 'differ', 'match', 'differ']
    
    for i, (digit, outcome) in enumerate(zip(test_digits, outcomes)):
        trade = bot.place_trade('match' if i % 2 == 0 else 'differ', 100, outcome)
        result = "✓ WON" if trade['won'] else "✗ LOST"
        print(f"   Trade {i+1}: {result} | Bet: {trade['bet_type']} | Outcome: {outcome} | "
              f"P/L: ${trade['payout']:.2f}")
    
    # Show statistics
    print("\n6. Bot Statistics:")
    stats = bot.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    example_usage()

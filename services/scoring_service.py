def get_score_label(score: float) -> str:
  if score >= 80:
    return "Excellent"
  if score >= 60:
    return "Good"
  if score >= 40:
    return "Average"
  return "Poor"


def get_score_color(score: float) -> str:
  if score >= 80:
    return "green"
  if score >= 60:
    return "blue"
  if score >= 40:
    return "yellow"
  return "red"


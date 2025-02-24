""" =============================================
* This func compares the betting value (line_score)
* to the program's prediction value
============================================= """

def predict(line_score, avg_value, n_a):
    try:
        # Convert inputs to float if they aren’t "--", handle empty strings or None
        ls = float(line_score) if line_score and line_score != n_a and line_score.strip() else None
        av = float(avg_value) if avg_value and avg_value != n_a and avg_value.strip() else None

        if ls is None or av is None:
            print(f"Debug - Predict returning n_a: line_score={line_score}, avg_value={avg_value}")
            return n_a

        if ls >= av:
            prediction = "Lower"
        else:
            prediction = "Higher"
        return prediction
    except (ValueError, TypeError) as e:
        print(f"Debug - Predict error: {e}, line_score={line_score}, avg_value={avg_value}")
        return n_a
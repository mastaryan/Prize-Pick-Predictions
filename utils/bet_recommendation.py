""" =============================================
* This func compares the betting value (line_score)
* to the program's prediction value
============================================= """

def predict(line_score, avg_value, n_a):
    try:
        # Convert inputs to float if they are numeric or strings, handle n_a ("--")
        ls = float(str(line_score).strip()) if line_score and line_score != n_a else None
        av = float(str(avg_value).strip()) if avg_value and avg_value != n_a else None

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
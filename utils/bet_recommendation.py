""" =============================================
* This func compares the betting value (line_score)
* to the program's prediction value
============================================= """

def predict(line_score, avg_value, n_a):
    try:
        # Convert inputs to float if they aren’t "--"
        ls = float(line_score) if line_score != n_a else None
        av = float(avg_value) if avg_value != n_a else None

        if ls is None or av is None:
            return n_a

        if ls >= av:
            prediction = "Lower"
        else:
            prediction = "Higher"
        return prediction
    except (ValueError, TypeError):
        return n_a
def examine_warnings(examinator):
    """Given an examinator function calls it as if the code was under with
    catch_warnings block. Useful for testing older Python versions"""
    import warnings
    warnings.simplefilter('default')
    with warnings.catch_warnings(record=True) as ws:
        examinator(ws)

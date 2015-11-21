def lcs(str1, str2):
    """
    Implementation of Longest Common Substring Algorithm
    Runs in O(nm)
    Taken from here:
    http://www.bogotobogo.com/python/python_longest_common_substring_lcs_algorithm_generalized_suffix_tree.php
    """
    m = len(str1)
    n = len(str2)
    counter = [[0] * (n + 1) for x in range(m + 1)]
    longest = 0
    lc_str = ''
    for i in range(m):
        for j in range(n):
            if str1[i] == str2[j]:
                c = counter[i][j] + 1
                counter[i + 1][j + 1] = c
                if c >= longest:
                    longest = c
                    lc_str = str1[i - c + 1:i + 1]

    return lc_str

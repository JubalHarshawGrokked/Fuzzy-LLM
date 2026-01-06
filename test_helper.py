from rewriter import rewrite_text


raw_text="John is pretty tall and quite fast I guess. So I was wondering, like, is he actually a good player or not? "
clean_text = rewrite_text(raw_text)


print(clean_text)
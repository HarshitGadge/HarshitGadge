# Beating the obvious baseline for high-cost Medicare members

*From [medicare-claims-analytics](https://github.com/HarshitGadge/medicare-claims-analytics).*

A care team can only call so many members a year. So the useful question isn't "how accurate is the model". It's "if we call the top 5% of members on a list, how many of next year's high-cost members do we reach?"

The obvious list ranks members by what they cost this year. It's simple, and it's a strong baseline, because expensive members often stay expensive.

My LightGBM model's 5% list finds **20.8%** of next year's high-cost members. Ranking by current spend finds **14.1%**. That's **+6.7 points**, with a 95% confidence interval of **+5.7 to +7.6**.

The model is only as good as the stays it learns from. Before counting anything, the dbt pipeline merges overlapping claims, same-day admissions and next-day transfers into single hospital stays. Without that step, one hospital visit can look like several, and readmissions get overcounted.

You can explore the results in the [live dashboard](https://hgadge-medicare-claims.streamlit.app).

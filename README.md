# Football Robot

---

This repository contains the source of [Football Robot](http://football-robot.com), the simple automated NFL football score predictor. The aim of this project was not to build a football score prediction model that was sophisticated (or even especially accurate). Instead, it was an attempt to build an ultra-lightweight and automated forecasting application that can run for almost no cost on AWS.

The Football Robot app is deployed to AWS via a CodePipeline-based CI/CD pipeline and deploys most of its infrastructure from a CloudFormation template. The predictions served by the application are automatically updated daily by a scheduled Lambda Function, and are written to a static website that is served via S3 static website hosting.

**Note:** The actual repo for development is in AWS CodeCommit. This public GitHub repo is for demonstration, and has specific AWS resource names in the CloudFormation template replaced with generic placeholders.

## The model

### Modeling teams and predicting scores

Predicted scores are produced by a model that rates the offensive and defensive strength of each NFL team. Specifically, for the offensive and defensive strengths for team $i$ are given by parameters $\alpha_i$ and $\beta_i$, respectively. Greater values for each parameter reflect greater strength.

When team $i$ plays team $j$, we model the final score attained by team $i$ by the random variable $s_{i} = \frac{\alpha_i}{\beta_j} + \frac{\epsilon}{\beta_j}$, where $\epsilon$ is a zero-mean Gaussian random variable with given variance. So, $s_i$ is Gaussian and has a mean determined by the combined offensive strength of team $i$ and defensive strength of team $j$. The expected score of team $i$ increases with increased offensive strength $\alpha_i$, and decreases with increased defensive strength of the opponent $\beta_j$. The variance in $s_i$ also determined by the defensive strength of team $j$. While the resulting heteroscedasticity is reasonable to expect in reality, it is introduced purely for analytical convenience.

The parameters $\alpha_i$ and $\beta_i$ for each team $i$ can be easily inferred from the outcomes of past games. Under the model described above, the scores also satisfy $s_i\beta_j - \alpha_i = \epsilon$. We could pose the problem of estimating $\alpha_i$ and $\beta_i$ for each team as the problem of finding values of these parameters that maximize the joint likelihood of the residual terms $\epsilon$ for all past games given the games' scores. However, this is problematic since simply setting all parameter values to zero maximizes the likelihood. To address this issue, we include the additional constraint that the defensive scores for all 32 teams need to sum to 32, or $\sum_i \beta_i = 32$.

So, if $\mathcal{G}$ is the set of pairs $(i,j)$ such that offense $i$ has played defense $j$ in a previous game, we aim to find parameters that minimize $\sum_{(i,j) \in \mathcal{G}} (s_i\beta_j - \alpha_i)^2$ subject to the constraint $\sum_i \beta_i = 32$. This is a linearly constrained least-squares problem, which has a simple closed-form solution.

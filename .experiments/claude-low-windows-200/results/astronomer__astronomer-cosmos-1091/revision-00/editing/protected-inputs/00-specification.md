add DatabricksOauthProfileMapping profile

## Description

As of now, Token-based auth is the only possible way to access databricks from cosmos, even though dbt-databricks support OAuth-based access as can be seen [here ](https://docs.getdbt.com/docs/core/connect-data-platform/databricks-setup).

This PR aims to enhance the support offered by cosmos to databricks. The final goal is to close #1085

I have tested locally and got a positive result. 
## Breaking Change?
No

## Checklist
- [X] I have made corresponding changes to the documentation (if required)
- [X] I have added tests that prove my fix is effective or that my feature works


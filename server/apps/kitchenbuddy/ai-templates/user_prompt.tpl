Parse the following HTML and extract the recipe information into a function call called "provide_recipe".

Each ingredient must be an object with separate name, amount, and modifier properties.
Prefer a numeric amount when possible; use a string when units or non-numeric wording are needed.
Put preparation adjectives in modifier, not in name.
Examples: { "name": "chicken breast", "amount": "1 lb", "modifier": "thinly sliced" }; { "name": "yellow onion", "amount": 2, "modifier": "" }; { "name": "butter", "amount": "1 stick", "modifier": "softened" }.

{{ html }}

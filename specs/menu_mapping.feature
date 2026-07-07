Feature: Enterprise Menu Data Parsing and Normalization
  As a POS Implementation Engineer
  I want the Parsing Agent to normalize chaotic, human-formatted Excel menus
  So that the data can be reliably converted into strict relational JSON for Infor POS without manual mapping.

  # RULE 1: The agent must fix human formatting by carrying parent data down to child rows.
  Scenario: Forward-filling missing Base Item definitions
    Given the ingested spreadsheet contains a row where "Base_Drink" is "Caffe Americano" and "Size" is "Tall"
    And the immediately following row has an empty or "NaN" value for "Base_Drink" but lists the "Size" as "Grande"
    When the Parsing Agent executes the structural normalization logic
    Then the second row must explicitly inherit "Caffe Americano" as its "Base_Drink"
    And the third row must explicitly inherit "Caffe Americano" if it lists "Venti"

  # RULE 2: The agent must respect the strict database rules for modifier mapping.
  Scenario: Enforcing the 'Applies_To' conditional modifier mapping
    Given the Parsing Agent has successfully identified a base product with the "Category" defined as "Cold Coffee"
    And the Modifiers reference table includes "Cold Foam" with an Applies_To value of "Cold Coffee"
    And the Modifiers reference table includes "Whipped Cream" with an Applies_To value of "Hot Coffee|Frappuccino"
    When the system maps allowed modifiers to the base product
    Then the payload must include "Cold Foam" as an allowed modifier
    And the payload must explicitly exclude "Whipped Cream"

  # RULE 3: The agent must cleanly handle spreadsheet artifacts and pricing defaults.
  Scenario: Safely handling empty rows and missing pricing
    Given the ingested spreadsheet contains a row where all core values are empty or "NaN"
    When the Parsing Agent processes the dataframe
    Then the empty row should be safely discarded without throwing an execution exception
    
  Scenario: Flagging zero-dollar base items
    Given a parsed base drink row has an empty, null, or "0.00" value in the "Base_Price" column
    When the Validation Agent reviews the parsed dataset
    Then the Validation Agent must flag the item as a "Pricing Schema Anomaly"
    And prevent the JSON payload from syncing to Infor POS

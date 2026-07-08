@auth
Feature: User authentication — Login and Logout
  As a registered user of the Real World App
  I want to log in with my credentials and log out when I'm done
  So that I can securely access my personal banking data and leave no session open behind me

  Background:
    Given the application is seeded with a known test user

  @smoke @critical @ui
  Scenario: Successful login redirects to the home page
    Given I am on the sign-in page
    When I sign in with valid credentials
    Then I should be redirected to the home page
    And a session cookie should be set

  @regression @ui
  Scenario: Logging in with "Remember me" persists the session
    Given I am on the sign-in page
    When I sign in with valid credentials and check "Remember me"
    Then I should be redirected to the home page
    And the session cookie should have an expiry date roughly 30 days out

  @smoke @regression @ui
  Scenario: Login fails with invalid credentials
    Given I am on the sign-in page
    When I sign in with an incorrect password
    Then I should see the error message "Username or password is invalid"
    And I should remain on the sign-in page

  @regression @ui
  Scenario Outline: Client-side validation blocks incomplete credentials
    Given I am on the sign-in page
    When I enter "<username>" as username and "<password>" as password
    Then I should see the validation message "<message>"
    And the sign-in button should be disabled

    Examples:
      | username | password | message                                       |
      |          | s3cret   | Username is required                          |
      | standard_user | abc | Password must contain at least 4 characters   |

  @smoke @critical @ui
  Scenario: Logged-in user can log out
    Given I am signed in
    When I sign out
    Then I should be redirected to the sign-in page
    And I should no longer be authenticated

  # API coverage for this story (POST /login, POST /logout, GET /checkAuth —
  # status codes, response schema, latency) lives in cypress/api/auth.api.cy.ts,
  # not here: the spec (section 3) keeps API specs physically separate from UI
  # specs so they can run first and independently, without going through the
  # BDD/Cucumber layer. See that file for the API-level scenarios.

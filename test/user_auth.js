const UserAuth = artifacts.require("UserAuth");

contract("UserAuth", accounts => {
  it("should register a user", async () => {
    const instance = await UserAuth.deployed();
    await instance.register("alice", "password123", { from: accounts[1] });
    const user = await instance.users(accounts[1]); // Access mapping directly
    assert.equal(user.exists, true, "User should be registered");
  });

  it("should update fraud status", async () => {
    const instance = await UserAuth.deployed();
    await instance.register("bob", "password456", { from: accounts[2] });
    await instance.updateFraudStatus(accounts[2], true, { from: accounts[0] });
    const isFraud = await instance.isUserFraudulent(accounts[2]); // Call view function
    assert.equal(isFraud, true, "User should be marked as fraudulent");
  });

  it("should block fraudulent user login", async () => {
    const instance = await UserAuth.deployed();
    const loginResult = await instance.login.call("bob", "password456", "2025-05-24", { from: accounts[2] }); // Use .call() for view function
    assert.equal(loginResult, false, "Fraudulent user should not login");
  });
});
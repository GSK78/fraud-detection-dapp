pragma solidity ^0.8.0;

contract UserAuth {
    struct User {
        bytes32 usernameHash;
        bytes32 passwordHash;
        bool exists;
        bool isFraudulent;
    }

    mapping(address => User) public users;
    address public owner;

    event UserRegistered(address indexed user, string username);
    event UserLoggedIn(address indexed user, string username, string time);
    event FraudStatusUpdated(address indexed user, bool isFraudulent);

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    function register(string memory username, string memory password) public {
        require(!users[msg.sender].exists, "User already exists");
        users[msg.sender] = User(
            keccak256(abi.encodePacked(username)),
            keccak256(abi.encodePacked(password)),
            true,
            false
        );
        emit UserRegistered(msg.sender, username);
    }

    function login(string memory username, string memory password, string memory time) public returns (bool) {
        User memory user = users[msg.sender];
        if (!user.exists) return false;
        if (user.isFraudulent) return false;
        if (
            user.usernameHash == keccak256(abi.encodePacked(username)) &&
            user.passwordHash == keccak256(abi.encodePacked(password))
        ) {
            emit UserLoggedIn(msg.sender, username, time);
            return true;
        }
        return false;
    }

    function updateFraudStatus(address userAddress, bool isFraud) public onlyOwner {
        require(users[userAddress].exists, "User does not exist");
        users[userAddress].isFraudulent = isFraud;
        emit FraudStatusUpdated(userAddress, isFraud);
    }

    function isUserFraudulent(address userAddress) public view returns (bool) {
        return users[userAddress].isFraudulent;
    }
}
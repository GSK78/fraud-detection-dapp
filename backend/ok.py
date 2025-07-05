import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from sklearn.metrics import classification_report, accuracy_score, roc_curve, auc
import joblib
import matplotlib.pyplot as plt
from web3 import Web3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
owner_address = os.getenv('OWNER_ADDRESS')
private_key = os.getenv('PRIVATE_KEY')

if not owner_address or not private_key:
    raise ValueError("OWNER_ADDRESS and PRIVATE_KEY must be set in .env file")

# Blockchain setup
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
if not w3.is_connected():
    raise ConnectionError("Failed to connect to Ethereum node")
print(f"Connected to blockchain. Latest block: {w3.eth.block_number}")

contract_address = '0x0127bc5cf311B88FD6e9349d0977b8Cf98C9862c'
contract_abi = [
    {
      "inputs": [],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "user",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "bool",
          "name": "isFraudulent",
          "type": "bool"
        }
      ],
      "name": "FraudStatusUpdated",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "user",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "username",
          "type": "string"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "time",
          "type": "string"
        }
      ],
      "name": "UserLoggedIn",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "user",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "string",
          "name": "username",
          "type": "string"
        }
      ],
      "name": "UserRegistered",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "owner",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function",
      "constant": True
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "name": "users",
      "outputs": [
        {
          "internalType": "bytes32",
          "name": "usernameHash",
          "type": "bytes32"
        },
        {
          "internalType": "bytes32",
          "name": "passwordHash",
          "type": "bytes32"
        },
        {
          "internalType": "bool",
          "name": "exists",
          "type": "bool"
        },
        {
          "internalType": "bool",
          "name": "isFraudulent",
          "type": "bool"
        }
      ],
      "stateMutability": "view",
      "type": "function",
      "constant": True
    },
    {
      "inputs": [
        {
          "internalType": "string",
          "name": "username",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "password",
          "type": "string"
        }
      ],
      "name": "register",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "string",
          "name": "username",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "password",
          "type": "string"
        },
        {
          "internalType": "string",
          "name": "time",
          "type": "string"
        }
      ],
      "name": "login",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "userAddress",
          "type": "address"
        },
        {
          "internalType": "bool",
          "name": "isFraud",
          "type": "bool"
        }
      ],
      "name": "updateFraudStatus",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "userAddress",
          "type": "address"
        }
      ],
      "name": "isUserFraudulent",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "view",
      "type": "function",
      "constant": True
    }
  ]
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Verify contract deployment and owner
code = w3.eth.get_code(contract_address)
if code == b'':
    raise ValueError(f"No contract found at {contract_address}. Redeploy the contract.")
print(f"Contract code at {contract_address}: {code.hex()}")

contract_owner = contract.functions.owner().call()
if contract_owner.lower() != owner_address.lower():
    raise ValueError(f"Owner mismatch: .env owner {owner_address}, contract owner {contract_owner}")

# Check owner balance
owner_balance = w3.eth.get_balance(owner_address)
print(f"Owner {owner_address} balance: {w3.from_wei(owner_balance, 'ether')} ETH")
if owner_balance < w3.to_wei(0.01, 'ether'):
    raise ValueError(f"Insufficient funds in {owner_address}. Required: 0.01 ETH")

try:
    print("Starting ML processing...")
    data = pd.read_csv(r"C:\Users\Shankar\Downloads\creditcard.csv")
    print("Dataset loaded successfully.")
    print("ML processing completed.")
except Exception as e:
    print(f"Error in ML section: {e}")

# Load dataset
file_path = r"C:\Users\Shankar\Downloads\creditcard.csv"
if not os.path.exists(file_path):
    raise FileNotFoundError(f"Dataset not found at: {file_path}")
data = pd.read_csv(file_path)

X = data.drop(columns=["Class"])
y = data["Class"]

scaler = StandardScaler()
X["Amount"] = scaler.fit_transform(X["Amount"].values.reshape(-1, 1))

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

smote = SMOTE(random_state=42)
X_train, y_train = smote.fit_resample(X_train, y_train)

model = RandomForestClassifier(random_state=42, n_estimators=100, max_depth=20)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)

print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred))

# Save model
model_path = r"C:\do\fraud-detection-dapp\savedresult\fraud_detection_model.pkl"
os.makedirs(os.path.dirname(model_path), exist_ok=True)
joblib.dump(model, model_path)
print(f"Model saved at: {model_path}")

# Save results
results = pd.DataFrame({'True Label': y_test, 'Predicted Label': y_pred})
excel_path = r"C:\do\fraud-detection-dapp\savedresult\fraudional_results.xlsx"
os.makedirs(os.path.dirname(excel_path), exist_ok=True)
results.to_excel(excel_path, index=False)
print(f"Results saved to: {excel_path}")

joblib.dump(X_test, r"C:\do\fraud-detection-dapp\savedresult\X_test.pkl")
joblib.dump(y_test, r"C:\do\fraud-detection-dapp\savedresult\y_test.pkl")

# Function to update fraud status
def update_fraud_status(user_address, is_fraud):
    try:
        # Check user balance
        user_balance = w3.eth.get_balance(user_address)
        print(f"User {user_address} balance: {w3.from_wei(user_balance, 'ether')} ETH")
        
        # Check if user is registered
        user = contract.functions.users(user_address).call()
        print(f"User {user_address} exists: {user[2]}, isFraud: {user[3]}")
        if not user[2]:
            print(f"User {user_address} not registered. Registering now...")
            user_private_key = "0xe7ff6305c3d4240284fe53dd9e291f11c968653ae4a8175efa6cf3ec88828194"
            if user_balance < w3.to_wei(0.01, 'ether'):
                print(f"Insufficient funds in {user_address} for registration")
                return None
            tx = contract.functions.register("testuser", "testpass").build_transaction({
                'from': user_address,
                'nonce': w3.eth.get_transaction_count(user_address),
                'gas': 3000000,
                'gasPrice': w3.to_wei('20', 'gwei')
            })
            signed_tx = w3.eth.account.sign_transaction(tx, user_private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"User {user_address} registered. Tx Hash: {tx_hash.hex()}")
            if receipt['status'] == 0:
                print("Registration transaction reverted")
                return None

        # Update fraud status
        tx = contract.functions.updateFraudStatus(user_address, is_fraud).build_transaction({
            'from': owner_address,
            'nonce': w3.eth.get_transaction_count(owner_address),  # Corrected typo
            'gas': 2000000,
            'gasPrice': w3.to_wei('20', 'gwei')
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] == 0:
            print("Fraud status update reverted")
        else:
            print(f"Fraud status updated for {user_address}. Tx Hash: {tx_hash.hex()}")
    except Exception as e:
        print(f"Error updating fraud status for {user_address}: {str(e)}")
        return None

# Assign user address to predictions
user_address = '0xa29FC23Fa33F1D3c566bD3459Ce17225EadF109A'
for i, pred in enumerate(y_pred):
    if pred == 1:  # Fraud detected
        update_fraud_status(user_address, True)

# Plot and save ROC curve
y_scores = model.predict_proba(X_test)[:, 1]
fpr, tpr, _ = roc_curve(y_test, y_scores)
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr, color='blue', label=f'ROC curve (area = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='red', linestyle='--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")
roc_path = r"C:\do\fraud-detection-dapp\savedresult\roc_curve.png"
os.makedirs(os.path.dirname(roc_path), exist_ok=True)
plt.savefig(roc_path)
print(f"ROC curve saved as {roc_path}")
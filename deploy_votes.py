import json
import requests
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class VotingConfig:
    """Configuration class for voting system parameters"""
    rpc_url: str
    private_key: str
    contract_address: str
    contract_abi_path: str = "Contract.abi.json"
    commit_file: str = "votes/commit.json"
    secrets_file: str = "votes/secrets.json"
    chain_id: int = 80002  # Polygon Mumbai Testnet
    gas_limit: int = 500_000
    max_retries: int = 3
    retry_delay: float = 1.0


class VotingSystemError(Exception):
    """Custom exception for voting system errors"""
    pass


class BlockchainVotingSystem:
    """Main class for blockchain voting operations"""

    def __init__(self, config: VotingConfig):
        self.config = config
        self._initialize_web3()
        self._load_contract()

    def _initialize_web3(self) -> None:
        """Initialize Web3 connection"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))
            if not self.w3.is_connected():
                raise VotingSystemError("Failed to connect to Ethereum node")

            self.admin_account = Account.from_key(self.config.private_key)
            logger.info(
                f"Web3 initialized successfully - RPC: {self.config.rpc_url}")
            logger.info(f"Admin account: {self.admin_account.address}")

        except Exception as e:
            raise VotingSystemError(f"Web3 initialization failed: {str(e)}")

    def _load_contract(self) -> None:
        """Load smart contract"""
        try:
            if not os.path.exists(self.config.contract_abi_path):
                raise VotingSystemError(
                    f"Contract ABI file not found: {self.config.contract_abi_path}")

            with open(self.config.contract_abi_path) as f:
                contract_abi = json.load(f)

            self.contract = self.w3.eth.contract(
                address=self.config.contract_address,
                abi=contract_abi
            )
            logger.info(f"Contract loaded at {self.config.contract_address}")

        except json.JSONDecodeError as e:
            raise VotingSystemError(f"Invalid JSON in ABI file: {str(e)}")
        except Exception as e:
            raise VotingSystemError(f"Contract loading failed: {str(e)}")

    def _get_gas_price(self) -> int:
        """Get current gas price with fallback"""
        try:
            gas_price = self.w3.eth.gas_price
            # Add 10% buffer for faster confirmation
            return int(gas_price * 1.1)
        except Exception as e:
            logger.warning(f"Failed to get gas price: {e}. Using fallback.")
            return self.w3.to_wei('20', 'gwei')

    def _send_transaction(self, tx_function, *args, **kwargs) -> str:
        """Send transaction with retry logic and better error handling"""
        nonce = self.w3.eth.get_transaction_count(self.admin_account.address)

        for attempt in range(self.config.max_retries):
            try:
                # Build transaction
                tx = tx_function(*args).build_transaction({
                    'from': self.admin_account.address,
                    'nonce': nonce,
                    'gas': self.config.gas_limit,
                    'gasPrice': self._get_gas_price(),
                    'chainId': self.config.chain_id,
                    **kwargs
                })

                # Sign and send transaction
                signed_tx = self.w3.eth.account.sign_transaction(
                    tx, private_key=self.admin_account.key)
                tx_hash = self.w3.eth.send_raw_transaction(
                    signed_tx.rawTransaction)

                # Wait for confirmation
                receipt = self.w3.eth.wait_for_transaction_receipt(
                    tx_hash, timeout=120)

                if receipt.status == 1:
                    logger.info(f"Transaction successful: {tx_hash.hex()}")
                    return tx_hash.hex()
                else:
                    raise VotingSystemError(
                        f"Transaction failed: {tx_hash.hex()}")

            except Exception as e:
                logger.warning(
                    f"Transaction attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
                    # Refresh nonce for retry
                    nonce = self.w3.eth.get_transaction_count(
                        self.admin_account.address)
                else:
                    raise VotingSystemError(
                        f"Transaction failed after {self.config.max_retries} attempts: {str(e)}")

    def _load_json_file(self, filepath: str) -> Dict:
        """Safely load JSON file with validation"""
        try:
            if not os.path.exists(filepath):
                raise VotingSystemError(f"File not found: {filepath}")

            with open(filepath, 'r') as f:
                data = json.load(f)

            if not isinstance(data, dict):
                raise VotingSystemError(f"Expected dictionary in {filepath}")

            return data

        except json.JSONDecodeError as e:
            raise VotingSystemError(f"Invalid JSON in {filepath}: {str(e)}")
        except Exception as e:
            raise VotingSystemError(f"Error loading {filepath}: {str(e)}")

    def add_candidates(self, candidates: List[str]) -> str:
        """Add candidates to the voting contract"""
        if not candidates:
            raise VotingSystemError("Candidates list cannot be empty")

        logger.info(f"Adding candidates: {candidates}")

        tx_hash = self._send_transaction(
            self.contract.functions.addCandidates,
            candidates
        )

        logger.info(f"Candidates added successfully: {tx_hash}")
        return tx_hash

    def commit_votes(self) -> List[str]:
        """Commit all votes from the commit file"""
        commit_data = self._load_json_file(self.config.commit_file)

        if not commit_data:
            raise VotingSystemError("No votes to commit")

        logger.info(f"Committing {len(commit_data)} votes")
        tx_hashes = []

        for user_id, vote_info in commit_data.items():
            try:
                # Validate vote data
                if 'vote_hash' not in vote_info or 'ipfs_cid' not in vote_info:
                    logger.error(f"Invalid vote data for user {user_id}")
                    continue

                vote_hash = Web3.to_bytes(hexstr=vote_info["vote_hash"])
                ipfs_cid = vote_info["ipfs_cid"]

                tx_hash = self._send_transaction(
                    self.contract.functions.commitVoteFor,
                    vote_hash, ipfs_cid, user_id
                )

                tx_hashes.append(tx_hash)
                logger.info(f"Vote committed for user {user_id}: {tx_hash}")

            except Exception as e:
                logger.error(
                    f"Failed to commit vote for user {user_id}: {str(e)}")
                continue

        logger.info(f"Successfully committed {len(tx_hashes)} votes")
        return tx_hashes

    def start_reveal_phase(self) -> str:
        """Start the reveal phase"""
        logger.info("Starting reveal phase")

        tx_hash = self._send_transaction(
            self.contract.functions.startRevealPhase
        )

        logger.info(f"Reveal phase started: {tx_hash}")
        return tx_hash

    def end_election(self) -> str:
        """End the election"""
        logger.info("Ending election")

        tx_hash = self._send_transaction(
            self.contract.functions.endElection
        )

        logger.info(f"Election ended: {tx_hash}")
        return tx_hash

    def reveal_votes(self) -> List[str]:
        """Reveal all votes"""
        # Start reveal phase first
        # self.start_reveal_phase()

        # Load data files
        commit_data = self._load_json_file(self.config.commit_file)
        secrets_data = self._load_json_file(self.config.secrets_file)

        if not secrets_data:
            raise VotingSystemError("No secrets to reveal")

        logger.info(f"Revealing {len(secrets_data)} votes")
        tx_hashes = []

        for user_id, secret_info in secrets_data.items():
            try:
                # Validate data
                if user_id not in commit_data:
                    logger.error(f"No commit found for user {user_id}")
                    continue

                if 'secret' not in secret_info or 'candidate_id' not in secret_info:
                    logger.error(f"Invalid secret data for user {user_id}")
                    continue

                secret = secret_info["secret"]
                candidate_id = str(secret_info["candidate_id"])
                vote_hash = Web3.to_bytes(
                    hexstr=commit_data[user_id]["vote_hash"])

                tx_hash = self._send_transaction(
                    self.contract.functions.revealVote,
                    vote_hash, candidate_id, secret
                )

                tx_hashes.append(tx_hash)
                logger.info(f"✅ Vote revealed for user {user_id}: {tx_hash}")

            except Exception as e:
                logger.error(
                    f"Failed to reveal vote for user {user_id}: {str(e)}")
                continue

        logger.info(f"Successfully revealed {len(tx_hashes)} votes")
        return tx_hashes

    def get_voting_results(self) -> Dict:
        """Get current voting results from the contract"""
        try:
            # This would depend on your contract's interface
            # Example implementation:
            results = {}
            # results = self.contract.functions.getResults().call()
            return results
        except Exception as e:
            logger.error(f"Failed to get voting results: {str(e)}")
            return {}


def create_config() -> VotingConfig:
    """Create configuration from environment variables"""
    required_vars = ['RPC_URL', 'PRIVATE_KEY', 'CONTRACT_ADDRESS']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        raise VotingSystemError(
            f"Missing required environment variables: {missing_vars}")

    return VotingConfig(
        rpc_url=os.getenv('RPC_URL'),
        private_key=os.getenv('PRIVATE_KEY'),
        contract_address=os.getenv('CONTRACT_ADDRESS')
    )


def main():
    """Main function with improved CLI interface"""
    try:
        config = create_config()
        voting_system = BlockchainVotingSystem(config)

        print("\n🗳️  Blockchain Voting System")
        print("=" * 40)
        print("Available actions:")
        print("1. add_candidates - Add candidates to the election")
        print("2. commit - Commit all votes")
        print("3. reveal - Start reveal phase and reveal all votes")
        print("4. results - Get current voting results")
        print("5. End Election - End the election and get final results")
        print("6. exit - Exit the program")
        print("=" * 40)

        while True:
            action = input(
                "\nEnter action (1-5 or action name): ").strip().lower()

            if action in ['1', 'add_candidates']:
                candidates_input = input(
                    "Enter candidates (comma-separated): ").strip()
                if candidates_input:
                    candidates = [c.strip()
                                  for c in candidates_input.split(',')]
                    voting_system.add_candidates(candidates)
                else:
                    # Default candidates for testing
                    voting_system.add_candidates(["1", "2"])

            elif action in ['2', 'commit']:
                voting_system.commit_votes()

            elif action in ['3', 'reveal']:
                voting_system.reveal_votes()

            elif action in ['4', 'results']:
                results = voting_system.get_voting_results()
                print(f"Voting results: {results}")

            elif action in ['5', 'end election']:
                voting_system.end_election()
                print("Election ended successfully.")

            elif action in ['6', 'exit']:
                print("Goodbye! 👋")
                break

            else:
                print("❌ Invalid action. Please choose 1-5 or use action names.")

    except VotingSystemError as e:
        logger.error(f"Voting system error: {str(e)}")
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Goodbye! 👋")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()

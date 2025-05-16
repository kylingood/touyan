from typing import Optional, Union

from eth_account.signers.local import LocalAccount
from eth_typing.evm import Address, ChecksumAddress
from web3 import Web3
from web3.types import TxParams, TxReceipt
from zksync2.core.types import EthBlockParams
from zksync2.manage_contracts.contract_encoder_base import ContractEncoder
from zksync2.module.zksync_module import ZkSync
from zksync2.signer.eth_signer import PrivateKeyEthSigner
from zksync2.transaction.transaction_builders import TxFunctionCall
from src.config.config import RPC_CONFIG
from src.config.config import config
from src.util.Desensitize import Desensitize

from loguru import logger

class TxExecutor:
    WAIT_TIME = config.get("WAIT_TIME")

    def __init__(
        self,
        contract_address: Union[Address, ChecksumAddress],
        contract_abi: dict,
        zk_web3: Web3,
        account: Optional[LocalAccount] = None,
    ) -> None:
        self.contract_address = zk_web3.to_checksum_address(contract_address)
        self.contract_abi = contract_abi
        self.zk_web3 = zk_web3
        self.zksync: ZkSync = self.zk_web3.zksync
        self.contract = zk_web3.eth.contract(address=contract_address, abi=contract_abi)
        self.account: LocalAccount = account
        self.chain_id = self.zksync.chain_id
        self.signer = PrivateKeyEthSigner(self.account, self.chain_id)
        self.deployed_address = None
        self.contract_encoder = ContractEncoder(
            web3=self.zk_web3, abi=self.contract_abi, bytecode=None
        )
        self.logger = logger

    # 执行合约方法
    # fn:合约方法名
    # args:合约方法参数
    def execute_method(self, fn, args, value=0, test=False, gas_limit=0) -> TxReceipt:
        zksync: ZkSync = self.zksync

        nonce = zksync.get_transaction_count(
            self.account.address, EthBlockParams.LATEST.value
        )
        gas_price = zksync.gas_price
        call_data = self.contract_encoder.encode_method(fn_name=fn, args=args)
        self.logger.debug(f"call_data: {call_data}")

        func_call = TxFunctionCall(
            chain_id=self.zk_web3.eth.chain_id,
            nonce=nonce,
            from_=self.account.address,
            to=self.contract_address,
            value=value,
            data=call_data,
            gas_limit=0,  # UNKNOWN AT THIS STATE,
            gas_price=gas_price,
        )

        estimate_gas = zksync.eth_estimate_gas(func_call.tx)
        self.logger.info(f"estimate_gas: {estimate_gas}")
        # 限制gas  主要针对era gas_limit 修改 限制gas消耗,降低成本
        if gas_limit != 0 and estimate_gas > gas_limit:
            self.logger.info(f"estimate_gas 被gas_limit传的值取代: {estimate_gas}")
            estimate_gas = gas_limit


        # estimate_gas = 1*10**9
        self.logger.info(
            f"Fee for transaction is: {estimate_gas} = {estimate_gas  /10**9} gwei"
        )

        self.logger.info(f"gas_price: {gas_price}")

        self.logger.info(f"price: {estimate_gas * gas_price/10**18}")

        tx_712 = func_call.tx712(estimate_gas)

        singed_message = self.signer.sign_typed_data(tx_712.to_eip712_struct())
        msg = tx_712.encode(singed_message)
        if test:
            return "0x"
        tx_hash = zksync.send_raw_transaction(msg)

        return tx_hash.hex()

    def handle_tx(self, tx_hash):
        self.logger.info(
            f"{Desensitize.desensitize_address(self.account.address)} swap_eth_to_usdc tx_hash:   {tx_hash}"
        )

        try:
            if tx_hash == "0x":
                return tx_hash, 1
            receipt = self.zksync.wait_for_transaction_receipt(
                transaction_hash=tx_hash, timeout=self.WAIT_TIME
            )
        except Exception as e:
            self.logger.info(
                f"{Desensitize.desensitize_address(self.account.address)} swap_eth_to_usdc receipt status:   {e}"
            )
            return tx_hash, -1
        self.logger.info(
            f"{Desensitize.desensitize_address(self.account.address)} swap_eth_to_usdc receipt status:   {receipt.get('status')}"
        )

        return tx_hash, receipt.get("status")


    def handle_linea_tx(self, tx_hash):
        self.logger.info(
            f"{Desensitize.desensitize_address(self.account.address)}  tx_hash:   {tx_hash}"
        )

        try:
            if tx_hash == "0x":
                return tx_hash, 1
            LINEA_PROVIDER = RPC_CONFIG["LINEA_PROVIDER"]
            eth_web3 = Web3(Web3.HTTPProvider(endpoint_uri=LINEA_PROVIDER))
            receipt = eth_web3.eth.get_transaction_receipt(tx_hash)

        except Exception as e:
            self.logger.info(
                f"{Desensitize.desensitize_address(self.account.address)}  receipt status:   {e}"
            )
            return tx_hash, -1

        self.logger.info(
            f"{Desensitize.desensitize_address(self.account.address)}  receipt status:   {receipt.get('status')}"
        )

        return tx_hash, receipt.get("status")



    def handle_linea_tx(self, tx_hash):
        self.logger.info(
            f"{Desensitize.desensitize_address(self.account.address)}  tx_hash:   {tx_hash}"
        )

        try:
            if tx_hash == "0x":
                return tx_hash, 1
            LINEA_PROVIDER = RPC_CONFIG["LINEA_PROVIDER"]
            eth_web3 = Web3(Web3.HTTPProvider(endpoint_uri=LINEA_PROVIDER))
            receipt = eth_web3.eth.get_transaction_receipt(tx_hash)

        except Exception as e:
            self.logger.info(
                f"{Desensitize.desensitize_address(self.account.address)}  receipt status:   {e}"
            )
            return tx_hash, -1

        self.logger.info(
            f"{Desensitize.desensitize_address(self.account.address)}  receipt status:   {receipt.get('status')}"
        )

        return tx_hash, receipt.get("status")

    def handle_arb_tx(self, tx_hash):
        self.logger.info(
            f"{Desensitize.desensitize_address(self.account.address)}  tx_hash:   {tx_hash}"
        )

        try:
            if tx_hash == "0x":
                return tx_hash, 1
            ARBITRUM_PROVIDER = RPC_CONFIG["ARBITRUM_PROVIDER"]
            eth_web3 = Web3(Web3.HTTPProvider(endpoint_uri=ARBITRUM_PROVIDER))
            receipt = eth_web3.eth.get_transaction_receipt(tx_hash)

        except Exception as e:
            self.logger.info(
                f"{Desensitize.desensitize_address(self.account.address)}  receipt status:   {e}"
            )
            return tx_hash, -1

        self.logger.info(
            f"{Desensitize.desensitize_address(self.account.address)}  receipt status:   {receipt.get('status')}"
        )

        return tx_hash, receipt.get("status")

    def handle_eth_tx(self, tx_hash):
        self.logger.info(
            f"{Desensitize.desensitize_address(self.account.address)}  tx_hash:   {tx_hash}"
        )

        try:
            if tx_hash == "0x":
                return tx_hash, 1

            #eth_endpoint_uri = 'https://mainnet.infura.io/v3/7c3026f1675647ceb90668277a199905'
            ETH_PROVIDER = RPC_CONFIG["ETH_PROVIDER"]
            eth_web3 = Web3(Web3.HTTPProvider(endpoint_uri=ETH_PROVIDER))
            receipt = eth_web3.eth.get_transaction_receipt(tx_hash)

        except Exception as e:
            self.logger.info(
                f"{Desensitize.desensitize_address(self.account.address)}  receipt status:   {e}"
            )
            return tx_hash, -1

        self.logger.info(
            f"{Desensitize.desensitize_address(self.account.address)}  receipt status:   {receipt.get('status')}"
        )

        return tx_hash, receipt.get("status")

    def call_method2(self, fn, args):
        return self.contract.functions[fn](*args).call()

    def call_method(self, fn, args):
        zksync: ZkSync = self.zksync
        encoded_get = self.contract_encoder.encode_method(fn_name=fn, args=args)
        eth_tx: TxParams = {
            # "from": self.account.address,
            "to": self.contract_address,
            "data": encoded_get,
        }
        eth_ret = zksync.call(eth_tx, EthBlockParams.LATEST.value)

        return eth_ret

from scripts.helpers import get_account
from brownie import interface, config, network, accounts


def main():
    get_weth()


def get_weth():
    """
    Mints WETH by depositing ETH
    """
    account = get_account()
    tx_details = {"from": account, "value": 0.1 * 1e18}
    active_network = config["networks"][network.show_active()]
    weth = interface.IWeth(active_network["weth_token"])
    tx = weth.deposit(tx_details)
    tx.wait(1)
    print("Recieved 0.1 WETH")
    return tx
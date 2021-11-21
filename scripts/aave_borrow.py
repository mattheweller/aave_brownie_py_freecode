from brownie import network, config, interface
from brownie import network, config, interface
from brownie.network import account
from scripts.helpers import get_account
from scripts.get_weth import get_weth
from web3 import Web3

#0.1 WETH
AMOUNT = Web3.toWei(0.1, "ether")
ACTIVE_NETWORK = config["networks"][network.show_active()]


def main():
    account = get_account()
    print(account.balance)
    erc20_address = ACTIVE_NETWORK["weth_token"]
    get_weth()
    lending_pool = get_lending_pool()
    approve_tx = approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)
    print("Depositing...")
    print(erc20_address)
    print(AMOUNT)
    print(account.address)

    tx = lending_pool.deposit(
        erc20_address, AMOUNT, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited!")
    # ... How much tho?
    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)
    print(f"Let's borrow {borrowable_eth}!")
    # DAI in terms of ETH:
    dai_eth_price = get_asset_price(ACTIVE_NETWORK["dai_eth_price_feed"])
    # borrowable_eth -> borrowable_dai * 95% (Don't want to get liquidated!)
    amount_dai_to_borrow = (1 / dai_eth_price) * (borrowable_eth * 0.95)
    print(f"We are going to borrow {amount_dai_to_borrow} DAI")
    dai_address = ACTIVE_NETWORK["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account}
    )
    borrow_tx.wait(1)
    print(f"We borrowed {amount_dai_to_borrow} DAI!")
    get_borrowable_data(lending_pool, account)
    repay_all(lending_pool, account)
    print(
        "You just deposited, borrowed, and repayed with Aave, Brownie, and Chainlink!"
    )


def get_lending_pool():
    lending_pool_address_provider = interface.ILendingPoolAddressesProvider(
        ACTIVE_NETWORK["lending_pool_addresses_provider"]
    )
    lending_pool_address = lending_pool_address_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool


def approve_erc20(amount, lending_pool, erc20_address, account):
    print("Approving ERC20 Token...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(lending_pool, amount, {"from": account})
    tx.wait(1)
    print("Approved!")
    return tx


def get_borrowable_data(lending_pool, account):
    # Got these from here: https://docs.aave.com/developers/the-core-protocol/lendingpool#getuseracountdata
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        loan_to_value,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)
    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
    print(f"You have {total_collateral_eth} worth of ETH deposited.")
    print(f"You have {total_debt_eth} worth of ETH borrowed.")
    print(f"You can borrow {available_borrow_eth} worth of ETH.")
    return (float(available_borrow_eth), float(total_debt_eth))


def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_latest_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_latest_price}")
    return float(converted_latest_price)


def repay_all(lending_pool, account):
    approve_erc20(
        Web3.toWei(AMOUNT, "ether"),
        lending_pool,
        ACTIVE_NETWORK["dai_token"],
        account,
    )
    repay_tx = lending_pool.repay(
        ACTIVE_NETWORK["dai_token"],
        AMOUNT,
        1,
        account.address,
        {"from": account},
    )
    repay_tx.wait(1)
    print("Repaid!")
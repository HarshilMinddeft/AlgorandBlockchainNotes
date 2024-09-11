import * as algokit from '@algorandfoundation/algokit-utils';
import { DISPENSER_ACCOUNT } from '@algorandfoundation/algokit-utils/types/account';
import { AlgoAmount } from '@algorandfoundation/algokit-utils/types/amount';
import { bytesToBigInt } from 'algosdk';

async function main() {
    const algorand = algokit.AlgorandClient.defaultLocalNet();

    const harshil = algorand.account.random();
    const secondacc = algorand.account.random();
    const dispenser = await algorand.account.dispenser();

    await algorand.send.payment({
        sender: dispenser.addr,
        receiver:harshil.addr,
        amount:algokit.algos(10)
    })
    // console.log("Harshil's Account=>",harshil)
    console.log("Fulldetailes", await algorand.account.getInformation(harshil.addr))

    const createResult = await algorand.send.assetCreate({
        sender:harshil.addr,
        total:100n
    })
    // console.log("Result==>>",createResult)
    const assetId = BigInt(createResult.confirmation.assetIndex!)
    console.log("AssetId",assetId)
    await algorand.send.payment({
        sender: dispenser.addr,
        receiver:secondacc.addr,
        amount:algokit.algos(10)
    })
 
    console.log("Balance before",await algorand.account.getInformation(secondacc.addr))

    await algorand.send.assetOptIn({
        sender:secondacc.addr,
        assetId
    })

    console.log("After balance", await algorand.account.getInformation(secondacc.addr))

    await algorand.send.assetTransfer({
        sender:harshil.addr,
        receiver:secondacc.addr,
        amount:8n,
        assetId
    })

    console.log("Harshil asset",await algorand.account.getAssetInformation(harshil.addr,assetId))
    console.log("secondacc asset",await algorand.account.getAssetInformation(secondacc.addr,assetId))
}   

main();
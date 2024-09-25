from algopy import *


class Steam(ARC4Contract):
    # State variables
    streamRate: UInt64  # MicroAlgos per second
    startTime: UInt64
    withdrawnAmount: UInt64
    recipient: Account  # Recipient account
    balance: UInt64  # Keep track of contract balance
    isStreaming: bool  # Track streaming status
    last_start_time: UInt64  # New variable to inspect the start time
    last_withdrawal_time: UInt64  # New variable to track last withdrawal time

    # Create application and initialize state variables
    @arc4.abimethod(allow_actions=["NoOp"], create="require")
    def createApplication(self) -> None:
        self.streamRate = UInt64(0)
        self.startTime = UInt64(0)
        self.withdrawnAmount = UInt64(0)
        self.recipient = Global.creator_address  # Set the creator initially
        self.balance = UInt64(0)
        self.isStreaming = bool(False)
        self.last_start_time = UInt64(0)  # Initialize last start time
        self.last_withdrawal_time = UInt64(0)  # Initialize last withdrawal time

    # Start a new stream
    @arc4.abimethod(allow_actions=["NoOp"])
    def startStream(self, recipient: Account, rate: UInt64, amount: UInt64) -> None:
        assert Txn.sender == Global.creator_address  # only creator can start

        # Store stream parameters
        self.recipient = recipient
        self.streamRate = rate
        self.startTime = Global.latest_timestamp
        self.withdrawnAmount = UInt64(0)
        self.balance += amount
        self.isStreaming = bool(True)
        # Store last start time for inspection
        self.last_start_time = self.startTime
        assert self.last_start_time > UInt64(0), "Start time must be greater than 0"

    # Calculate the total streamed amount
    @subroutine
    def _calculateStreamedAmount(self) -> UInt64:
        elapsed_time = Global.latest_timestamp - self.startTime
        total_streamed = elapsed_time * self.streamRate
        return total_streamed - self.withdrawnAmount

    # Withdraw funds for the recipient based on the streamed amount
    @arc4.abimethod(allow_actions=["NoOp"])
    def withdraw(self, amount: UInt64) -> None:
        assert Txn.sender == self.recipient  # Only the recipient can withdraw

        available_amount = self._calculateStreamedAmount()

        assert (
            amount <= available_amount
        ), "Requested withdrawal exceeds available amount"  # Custom error message

        elapsed_since_last_withdrawal = (
            Global.latest_timestamp - self.last_withdrawal_time
        )
        assert elapsed_since_last_withdrawal >= UInt64(
            2
        ), "Withdrawal can only occur every 2 second"  # Adjust as needed

        # Ensure the requested amount is valid based on the elapsed time since the last withdrawal
        amount_since_last_withdrawal = elapsed_since_last_withdrawal * self.streamRate
        assert (
            amount
            <= available_amount - self.withdrawnAmount + amount_since_last_withdrawal
        ), "Requested amount exceeds available streamed amount based on time passed"

        # Update the last withdrawal time
        self.last_withdrawal_time = Global.latest_timestamp

        # Ensure there's enough to withdraw
        self.withdrawnAmount += amount  # Update the withdrawn amount
        self.balance -= amount

        itxn.InnerTransaction(
            sender=Global.current_application_address,
            receiver=self.recipient,
            amount=amount,
            note=b"Withdrawal from contract",
            type=TransactionType.Payment,
        ).submit()

    # Stop the stream and transfer any remaining balance back to the creator
    @arc4.abimethod(allow_actions=["NoOp"])
    def stopStream(self) -> None:
        assert Txn.sender == Global.creator_address  # Only creator can stop

        # Reset stream parameters
        self.streamRate = UInt64(0)
        self.isStreaming = bool(False)

        # Transfer remaining funds back to the creator
        if self.balance > 0:
            itxn.Payment(
                receiver=Global.creator_address,
                amount=self.balance,
                close_remainder_to=Global.creator_address,
            ).submit()
            self.balance = UInt64(0)

    # # Optional: Pause the stream
    # @arc4.abimethod(allow_actions=["NoOp"])
    # def pauseStream(self) -> None:
    #     assert Txn.sender == self.recipient  # Only recipient can pause
    #     assert self.isStreaming  # Stream must be active
    #     self.isStreaming = bool(False)  # Pause the stream

    # # Optional: Resume the stream
    # @arc4.abimethod(allow_actions=["NoOp"])
    # def resumeStream(self) -> None:
    #     assert Txn.sender == self.recipient  # Only recipient can resume
    #     assert not self.isStreaming  # Stream must be paused
    #     self.isStreaming = bool(True)  # Resume the stream
    #     self.startTime = Global.latest_timestamp  # Reset start time

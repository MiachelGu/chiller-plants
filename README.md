# Analysis of Kaer's Chiller Plants


## Record
```txt
Set A Experiments. CWSHDR forecast.

    LSTM. Layer 1: 15 Nodes, Layer 2: 10 Nodes, Adam + MSE. 100 Epochs
    Log Dir: Kaer2
    Features: ["loadsys", "drybulb", "rh", "cwrhdr", "cwsfhdr"]
    Opinion: Okay-ish. These NNs are such a black-boxes. Unable to trust.

    LSTM. Layer 1: 15 Nodes, Layer 2: 10 Nodes, Adam + MSE. 100 Epochs
    Used first derivative as dataset.
    Log Dir: Kaer3
    Features: ["loadsys", "drybulb", "rh", "cwrhdr", "cwsfhdr"]
    Opinion: Looks like overfitting. Converged relatively faster.



Set C Experiments. External Conditions.

    Log Dir: Keras12
    LSTM: Layer 1: 15, Layer 2: 10
    features = ["drybulb", "rh", "hour", "weekend"]
    target = ["loadsys"]
    Opinion: Eeeeeeee!


```
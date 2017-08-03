# Analysis of Kaer's Chiller Plants


## Record
```txt
Set A Experiments:
Explore simple normalized data

Experiment 0:

    LSTM Trail run. Layer 1: 15 Nodes, Layer 2: 10 Nodes, Adam + MSE
    Log Dir: Kaer1
    Features: ["loadsys", "drybulb", "rh", "cwrhdr", "cwsfhdr"]
    Opinion: Aborted after few epochs.

Experiment 1:
    LSTM. Layer 1: 15 Nodes, Layer 2: 10 Nodes, Adam + MSE. 100 Epochs
    Log Dir: Kaer2
    Features: ["loadsys", "drybulb", "rh", "cwrhdr", "cwsfhdr"]
    Opinion: Okay-ish. These NNs are such a black-boxes. Unable to trust.

Experiment 2:
    LSTM. Layer 1: 15 Nodes, Layer 2: 10 Nodes, Adam + MSE. 100 Epochs
    Used first derivative as dataset.
    Log Dir: Kaer3
    Features: ["loadsys", "drybulb", "rh", "cwrhdr", "cwsfhdr"]
    Opinion: Looks like overfitting. Converged relatively faster.

Experiment 3:
    LSTM. Layer 1: 15 Nodes, Layer 2: 10 Nodes, Adam + MSE. 100 Epochs
    Used first derivative as dataset. Replaced sudden peaks with medians.
    Log Dir: Kaer4
    Features: ["loadsys", "drybulb", "rh", "cwrhdr", "cwsfhdr"]
    Opinion: The validation & test metrics are crazily different. The
        validation plot looks flat! I need to increase the size. Currently its
        just 1 week data.

Experiment 4:
    LSTM. Layer 1: 24 * 3, Layer 2: 24, Layer 3: 8
    Log Dir: kaer5. 20+ Eochs. Aborted.
    Features: ["loadsys", "drybulb", "rh", "ct1kw", "ct2akw"], Lookback: 8
    Opinion: Oh Shit, this overfitting is through the roof! Perhaps, my 
        initial interpretation is correct.. that a complex network isn't needed.

Experiment 5:
    LSTM. Layer 1: 24 * 3. Just one Layer this time.. Keeping everything same as in Exp 4.
    Log Dir: kaer6
    Opinion: I think the issue is with CTKW. That's a useless parameter indeed.

Experiment 6:
    Network same as in Exp 5. 
    Features: ["loadsys", "drybulb", "rh",]
    Log Dir: Kaer7
    Opinion: Looks like, needs lots of learnings and some more layers. Aborting now.


Set B Experiments:
Expore decomposed data.

Experiment 7:
    LSTM: Layer 1: 32*3, Layer 2: 32, Layer 3: 4.
    Features: ["loadsys_seasonal", "drybulb_seasonal", "rh_seasonal", "cwrhdr_seasonal"]
    Target: ["cwshdr_seasonal"]
    Log Dir: Kaer8. First 100 epochs represent different architecture.. Ignore that!
    Opinion: Looks like it generalized decently, but its not up to the expectations.

    LSTM: Layer 1: 32*3, Layer 2: 32, Layer 3: 4.
    Features: ["loadsys_resid", "drybulb_resid", "rh_resid", "cwrhdr_resid"]
    Target: ["cwshdr_resid"]
    Log Dir: Kaer9
    Opinion: Shit.. 

    LSTM: Layer 1: 70
    Features: ["loadsys_resid", "drybulb_resid", "rh_resid", "ctkw_resid"]
    Target: ["cwshdr_resid"]
    Log Dir: Kaer10. Mixed with several models. 
    Opinion: Another shit

    LSTM: Layer 1: 70
    Features: ["loadsys_resid", "drybulb_resid", "rh_resid", "cwrhdr_resid"]
    Target: ["cwshdr_resid"]
    Log Dir: Kaer11
    Opinion: Gosh, I forgot to ensure the data to Keras is normalized..
        The residue is able to give decent MAPE.

```
# Librecorder

Librecorder is a free-libre platform for AI and algorithmic diagnostic analysis at point-of-care in low-resource settings.
It provides shared case management, image storage and a plug-in framework, so a new diagnostic algorithm is a single module rather than a whole new instrument.

The url to the live instance of Librecoder is: [https://microlab.parccommons.org/](https://microlab.parccommons.org/).

# Where do I start?

| I want to... | Go to |
|---|---|
| Run Librecorder on my computer | [docs/setup.md](docs/setup.md) |
| Understand how it works | [docs/architecture.md](docs/architecture.md) |
| Experiment with my own model or data | [docs/research/](docs/research/README.md) |
| Contribute code (classifiers, backend, UI) | [CONTRIBUTING.md](CONTRIBUTING.md) |

# Quick start

```
git clone https://github.com/PubInv/librecorder.git
cd librecorder
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd Software/WebApp && python app.py
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000). See [docs/setup.md](docs/setup.md) for Windows, conda and troubleshooting.

# Motivation
After acting as a judge at the Rice360 Annual Global Health Technologies Design Competition several years in a row, 
I kept seeing similar projects using overlapping hardware and software.
Many projects consist of a sensor read by a microcontroller or a microcomputer and acted upon by software.
Project after project invests again and again in making an enclosure for a small computer, making an 
independent instrument which is not shared with any other projects.
Librecorder is an attempt to solve this inefficiency through the principles open source software and hardware, which
emphasizes modularity, sharing and reuse. This has been called "The Unix Way". 
We intend to share sensors such as cameras, letting them be 
used for multiple diagnostic purposes, running on shared hardware, using a shared case managment system and 
software presentation system.

In the future, rather than creating stand-alone instruments, researchers will focus on what matters: creating
one new module that has the kernel of their innovation. The rest will be done for them.
Each module will enhance the total suite of the librecorder. 
This will create an open-source tool that eventually will be able to diagnose a very large number of 
medical conditions or risk conditions. The idea is to create the "medical tricorder" from the original Star Trek
television series.

Librecorder is a platform for AI and algorithmic diagnostic analysis at point-of-care in low-resource settings.
The idea is to make a free-libre platform consisting of a small portable computer, a variety of sensors,
and, most of all, a framework for slotting in new software algorithms and AI neural networks which
offer an ever-expanding set of diagnostic functions.

# Architecture
Below is a diagram of the envisioned architecture. For more on how the code works today, see [docs/architecture.md](docs/architecture.md).
<img width="960" height="720" alt="Architecture #1 (1)" src="https://github.com/user-attachments/assets/69e6bbe8-6755-4211-b50c-f9f0e4918d16" />

# References

* The HealthyPI project is very similar to this project: [https://www.opensourceimaging.org/project/protocentral-healthypi/]( https://www.opensourceimaging.org/project/protocentral-healthypi/)

# License

Librecorder is licensed under the [GNU Affero General Public License v3.0](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md) for what this means for contributors.

Librecorder is a [Public Invention](https://www.pubinv.org/) project.

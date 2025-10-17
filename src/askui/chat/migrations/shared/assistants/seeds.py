import platform
import sys

from askui.chat.migrations.shared.assistants.models import AssistantV1
from askui.chat.migrations.shared.utils import now_v1

COMPUTER_AGENT_V1 = AssistantV1(
    id="asst_68ac2c4edc4b2f27faa5a253",
    created_at=now_v1(),
    name="Computer Agent",
    avatar="data:image/webp;base64,UklGRswRAABXRUJQVlA4WAoAAAA4AAAAPwAAPwAASUNDUEgMAAAAAAxITGlubwIQAABtbnRyUkdCIFhZWiAHzgACAAkABgAxAABhY3NwTVNGVAAAAABJRUMgc1JHQgAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLUhQICAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABFjcHJ0AAABUAAAADNkZXNjAAABhAAAAGx3dHB0AAAB8AAAABRia3B0AAACBAAAABRyWFlaAAACGAAAABRnWFlaAAACLAAAABRiWFlaAAACQAAAABRkbW5kAAACVAAAAHBkbWRkAAACxAAAAIh2dWVkAAADTAAAAIZ2aWV3AAAD1AAAACRsdW1pAAAD+AAAABRtZWFzAAAEDAAAACR0ZWNoAAAEMAAAAAxyVFJDAAAEPAAACAxnVFJDAAAEPAAACAxiVFJDAAAEPAAACAx0ZXh0AAAAAENvcHlyaWdodCAoYykgMTk5OCBIZXdsZXR0LVBhY2thcmQgQ29tcGFueQAAZGVzYwAAAAAAAAASc1JHQiBJRUM2MTk2Ni0yLjEAAAAAAAAAAAAAABJzUkdCIElFQzYxOTY2LTIuMQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWFlaIAAAAAAAAPNRAAEAAAABFsxYWVogAAAAAAAAAAAAAAAAAAAAAFhZWiAAAAAAAABvogAAOPUAAAOQWFlaIAAAAAAAAGKZAAC3hQAAGNpYWVogAAAAAAAAJKAAAA+EAAC2z2Rlc2MAAAAAAAAAFklFQyBodHRwOi8vd3d3LmllYy5jaAAAAAAAAAAAAAAAFklFQyBodHRwOi8vd3d3LmllYy5jaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABkZXNjAAAAAAAAAC5JRUMgNjE5NjYtMi4xIERlZmF1bHQgUkdCIGNvbG91ciBzcGFjZSAtIHNSR0IAAAAAAAAAAAAAAC5JRUMgNjE5NjYtMi4xIERlZmF1bHQgUkdCIGNvbG91ciBzcGFjZSAtIHNSR0IAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZGVzYwAAAAAAAAAsUmVmZXJlbmNlIFZpZXdpbmcgQ29uZGl0aW9uIGluIElFQzYxOTY2LTIuMQAAAAAAAAAAAAAALFJlZmVyZW5jZSBWaWV3aW5nIENvbmRpdGlvbiBpbiBJRUM2MTk2Ni0yLjEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHZpZXcAAAAAABOk/gAUXy4AEM8UAAPtzAAEEwsAA1yeAAAAAVhZWiAAAAAAAEwJVgBQAAAAVx/nbWVhcwAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAo8AAAACc2lnIAAAAABDUlQgY3VydgAAAAAAAAQAAAAABQAKAA8AFAAZAB4AIwAoAC0AMgA3ADsAQABFAEoATwBUAFkAXgBjAGgAbQByAHcAfACBAIYAiwCQAJUAmgCfAKQAqQCuALIAtwC8AMEAxgDLANAA1QDbAOAA5QDrAPAA9gD7AQEBBwENARMBGQEfASUBKwEyATgBPgFFAUwBUgFZAWABZwFuAXUBfAGDAYsBkgGaAaEBqQGxAbkBwQHJAdEB2QHhAekB8gH6AgMCDAIUAh0CJgIvAjgCQQJLAlQCXQJnAnECegKEAo4CmAKiAqwCtgLBAssC1QLgAusC9QMAAwsDFgMhAy0DOANDA08DWgNmA3IDfgOKA5YDogOuA7oDxwPTA+AD7AP5BAYEEwQgBC0EOwRIBFUEYwRxBH4EjASaBKgEtgTEBNME4QTwBP4FDQUcBSsFOgVJBVgFZwV3BYYFlgWmBbUFxQXVBeUF9gYGBhYGJwY3BkgGWQZqBnsGjAadBq8GwAbRBuMG9QcHBxkHKwc9B08HYQd0B4YHmQesB78H0gflB/gICwgfCDIIRghaCG4IggiWCKoIvgjSCOcI+wkQCSUJOglPCWQJeQmPCaQJugnPCeUJ+woRCicKPQpUCmoKgQqYCq4KxQrcCvMLCwsiCzkLUQtpC4ALmAuwC8gL4Qv5DBIMKgxDDFwMdQyODKcMwAzZDPMNDQ0mDUANWg10DY4NqQ3DDd4N+A4TDi4OSQ5kDn8Omw62DtIO7g8JDyUPQQ9eD3oPlg+zD88P7BAJECYQQxBhEH4QmxC5ENcQ9RETETERTxFtEYwRqhHJEegSBxImEkUSZBKEEqMSwxLjEwMTIxNDE2MTgxOkE8UT5RQGFCcUSRRqFIsUrRTOFPAVEhU0FVYVeBWbFb0V4BYDFiYWSRZsFo8WshbWFvoXHRdBF2UXiReuF9IX9xgbGEAYZRiKGK8Y1Rj6GSAZRRlrGZEZtxndGgQaKhpRGncanhrFGuwbFBs7G2MbihuyG9ocAhwqHFIcexyjHMwc9R0eHUcdcB2ZHcMd7B4WHkAeah6UHr4e6R8THz4faR+UH78f6iAVIEEgbCCYIMQg8CEcIUghdSGhIc4h+yInIlUigiKvIt0jCiM4I2YjlCPCI/AkHyRNJHwkqyTaJQklOCVoJZclxyX3JicmVyaHJrcm6CcYJ0kneierJ9woDSg/KHEooijUKQYpOClrKZ0p0CoCKjUqaCqbKs8rAis2K2krnSvRLAUsOSxuLKIs1y0MLUEtdi2rLeEuFi5MLoIuty7uLyQvWi+RL8cv/jA1MGwwpDDbMRIxSjGCMbox8jIqMmMymzLUMw0zRjN/M7gz8TQrNGU0njTYNRM1TTWHNcI1/TY3NnI2rjbpNyQ3YDecN9c4FDhQOIw4yDkFOUI5fzm8Ofk6Njp0OrI67zstO2s7qjvoPCc8ZTykPOM9Ij1hPaE94D4gPmA+oD7gPyE/YT+iP+JAI0BkQKZA50EpQWpBrEHuQjBCckK1QvdDOkN9Q8BEA0RHRIpEzkUSRVVFmkXeRiJGZ0arRvBHNUd7R8BIBUhLSJFI10kdSWNJqUnwSjdKfUrESwxLU0uaS+JMKkxyTLpNAk1KTZNN3E4lTm5Ot08AT0lPk0/dUCdQcVC7UQZRUFGbUeZSMVJ8UsdTE1NfU6pT9lRCVI9U21UoVXVVwlYPVlxWqVb3V0RXklfgWC9YfVjLWRpZaVm4WgdaVlqmWvVbRVuVW+VcNVyGXNZdJ114XcleGl5sXr1fD19hX7NgBWBXYKpg/GFPYaJh9WJJYpxi8GNDY5dj62RAZJRk6WU9ZZJl52Y9ZpJm6Gc9Z5Nn6Wg/aJZo7GlDaZpp8WpIap9q92tPa6dr/2xXbK9tCG1gbbluEm5rbsRvHm94b9FwK3CGcOBxOnGVcfByS3KmcwFzXXO4dBR0cHTMdSh1hXXhdj52m3b4d1Z3s3gReG54zHkqeYl553pGeqV7BHtje8J8IXyBfOF9QX2hfgF+Yn7CfyN/hH/lgEeAqIEKgWuBzYIwgpKC9INXg7qEHYSAhOOFR4Wrhg6GcobXhzuHn4gEiGmIzokziZmJ/opkisqLMIuWi/yMY4zKjTGNmI3/jmaOzo82j56QBpBukNaRP5GokhGSepLjk02TtpQglIqU9JVflcmWNJaflwqXdZfgmEyYuJkkmZCZ/JpomtWbQpuvnByciZz3nWSd0p5Anq6fHZ+Ln/qgaaDYoUehtqImopajBqN2o+akVqTHpTilqaYapoum/adup+CoUqjEqTepqaocqo+rAqt1q+msXKzQrUStuK4trqGvFq+LsACwdbDqsWCx1rJLssKzOLOutCW0nLUTtYq2AbZ5tvC3aLfguFm40blKucK6O7q1uy67p7whvJu9Fb2Pvgq+hL7/v3q/9cBwwOzBZ8Hjwl/C28NYw9TEUcTOxUvFyMZGxsPHQce/yD3IvMk6ybnKOMq3yzbLtsw1zLXNNc21zjbOts83z7jQOdC60TzRvtI/0sHTRNPG1EnUy9VO1dHWVdbY11zX4Nhk2OjZbNnx2nba+9uA3AXcit0Q3ZbeHN6i3ynfr+A24L3hROHM4lPi2+Nj4+vkc+T85YTmDeaW5x/nqegy6LzpRunQ6lvq5etw6/vshu0R7ZzuKO6070DvzPBY8OXxcvH/8ozzGfOn9DT0wvVQ9d72bfb794r4Gfio+Tj5x/pX+uf7d/wH/Jj9Kf26/kv+3P9t//9BTFBISgIAAAGQRFubIUmRKLRt27btXo3tmZVtGyvbtm3btm1PKf9hRNQ/2kbEBJD/XtEzJDTSW/59UqZfffjo2bUV7dx+D8uOD+CXO2N+B8eZBqA8EfEbdAT6lXboHA4zKH3Q5bxngDsh2BooLEpzbK2AeQIy13VsA5DVUdiaIyv6wPQqA5n9YRbjWEtkZBTL8SAZW+YbOkN/Gwmb3SG6k6EaAZv1AboF9hLB7nqJ6lVNtYAu/Q3N255OEsHraPOTMUA7I1AroLFsf2pbdHBFQbtXNGeKnCSC0jK2dt0lBoCLd3Sf9EC7LFojYBCb7H5qNAFX3WofgjB07Hsw46K6bXpNTDZPnRtgXiMAnPY3R41ngLGtGYIvA8ozsdwsZwHSmw15NdBjgUfJnKYB3h1+XByPI4K5Wh7xLzG9z+NR/BmTsSaPeiZM7zJ49AHMpnY8xqGCCwlsmnW44HZPZxbvm8hA2R3H4HICG8AyLR3pge9J+O/2OIxOtQbfgyA6/9v4nkXSxb3Cdz+IzvUMvqcRdGQovvuBDFV6bKbhMoP7MWzX/AlrTNdBG3WYJqiZCCGWoxQ8t5IEHsTtCJ4jToRv5VUFy3SJEwndhaUz4d7OhONdEb8en42KguCol8it5sW3egwLrPhZZLUYMGnD1TeKmbpLArefar0zWq5+qtPr9XqdTvfl86dPHz+8f/fm5dOH927duH7l4rpIgZjfMqasqrqqsry8vLQwPz8vKyMtJS4yJMDHy9PNxZL8FQVBlCRZlmWVxlIjyGqNVqsSCSGCyAJWUDggmAIAAPAPAJ0BKkAAQAA+kTyZSaWjIiEoG/tQsBIJZwDJ+FvKFv67tp+RMGNcDv9lccKdO60gqH5MeC/EtYd0zUOkfunNPYDWjWiNhmKAoXQQo+GDUJN88TbmU3UWr3+Ddvu5s2Eukjyw96p2S2tDw6aI0pTAjeRIQ6n3XnUckPx9C41nFxlceofxDAAA/v02dN7UOf8yY/rkv0FMLUFIHHa9HnubqLmPG/0PkUpWsuTIsdDzQ+GNLWeNexqbAVHtbBcjuWw7309/2TyreZ4Urf9AIlZhs2YdWHB63q32OItvwlhMbe45JBwS+01b8Kv8Kys6xPiAbY2ffwyrFZto2clrktrTUGODsZj+xsiMg2gl61QSCU6DPDV/rkv4TSw71kah9dNnmusKgQ6kYtkXRrTI2mInVps+WK5IPA2358a8ksYj5rE4xoPWHkFx9zSZhyReGaEAObqnmScxyOC4U7O6+B4L26wEbKNLu3shOv9rwGNJuEpkB37Cke7M2WB0728OvDtbU/JtjA5E11BzeNp6Ax2+fOFvC+MGMvSevWynClCPHHT2nmylDPSwOCcGMx6g/q57JifzellyZiU/g448apyvOPqLjdWJLujKS6TyCoYSsLf9FeE6vFMZIPAIZaTR4gkqNvwkooY+t8DeCa+herqzE9IGXG7duDTcPz2sJaW6kgcDWu2IJ9413Lh+puu4DoZmBclBMEyfdFEGHOpjQAnQsrjckgWfbAqWF6+FaKFVf1hTeuhWERcMd9nNw2aRrKCxWia1VJTU0FQEPUG2osZQtEKcCIlcCWB4LurhOl1hs98Rqpu5ghk+cTd/ToGo12tm/Zmd+5O+j8XtgDIwF/NTWiHsPRndZq58MnOxBkOAaYBLYHRAAABFWElGbAAAAE1NACoAAAAQRXhpZk1ldGEABQEaAAUAAAABAAAAUgEbAAUAAAABAAAAWgEoAAMAAAABAAIAAAExAAIAAAAKAAAAYgITAAMAAAABAAEAAAAAAAAAAABIAAAAAQAAAEgAAAABZXpnaWYuY29tAA==",
    system=(
        f"""<SYSTEM_CAPABILITY>
* You are utilising a {sys.platform} machine using {platform.machine()} architecture with internet access.
* When you cannot find something (application window, ui element etc.) on the currently selected/active displa/screen, check the other available displays by listing them and checking which one is currently active and then going through the other displays one by one until you find it or you have checked all of them.
* When asked to perform web tasks try to open the browser (firefox, chrome, safari, ...) if not already open. Often you can find the browser icons in the toolbars of the operating systems.
* When viewing a page it can be helpful to zoom out/in so that you can see everything on the page. Either that, or make sure you scroll down/up to see everything before deciding something isn't available.
* When using your function calls, they take a while to run and send back to you. Where possible/feasible, try to chain multiple of these calls all into one function calls request.
</SYSTEM_CAPABILITY>

<IMPORTANT>
* When using Firefox, if a startup wizard appears, IGNORE IT.  Do not even click "skip this step".  Instead, click on the address bar where it says "Search or enter address", and enter the appropriate search term or URL there.
* If the item you are looking at is a pdf, if after taking a single screenshot of the pdf it seems that you want to read the entire document instead of trying to continue to read the pdf from your screenshots + navigation, determine the URL, use curl to download the pdf, install and use pdftotext to convert it to a text file, and then read that text file directly with your StrReplaceEditTool.
</IMPORTANT>"""
    ),
    tools=[
        "computer",
        "list_displays",
        "set_active_display",
        "retrieve_active_display",
    ],
)

ANDROID_AGENT_V1 = AssistantV1(
    id="asst_68ac2c4edc4b2f27faa5a255",
    created_at=now_v1(),
    name="Android Agent",
    avatar="data:image/webp;base64,UklGRoIRAABXRUJQVlA4WAoAAAA4AAAAPwAAPwAASUNDUEgMAAAAAAxITGlubwIQAABtbnRyUkdCIFhZWiAHzgACAAkABgAxAABhY3NwTVNGVAAAAABJRUMgc1JHQgAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLUhQICAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABFjcHJ0AAABUAAAADNkZXNjAAABhAAAAGx3dHB0AAAB8AAAABRia3B0AAACBAAAABRyWFlaAAACGAAAABRnWFlaAAACLAAAABRiWFlaAAACQAAAABRkbW5kAAACVAAAAHBkbWRkAAACxAAAAIh2dWVkAAADTAAAAIZ2aWV3AAAD1AAAACRsdW1pAAAD+AAAABRtZWFzAAAEDAAAACR0ZWNoAAAEMAAAAAxyVFJDAAAEPAAACAxnVFJDAAAEPAAACAxiVFJDAAAEPAAACAx0ZXh0AAAAAENvcHlyaWdodCAoYykgMTk5OCBIZXdsZXR0LVBhY2thcmQgQ29tcGFueQAAZGVzYwAAAAAAAAASc1JHQiBJRUM2MTk2Ni0yLjEAAAAAAAAAAAAAABJzUkdCIElFQzYxOTY2LTIuMQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAWFlaIAAAAAAAAPNRAAEAAAABFsxYWVogAAAAAAAAAAAAAAAAAAAAAFhZWiAAAAAAAABvogAAOPUAAAOQWFlaIAAAAAAAAGKZAAC3hQAAGNpYWVogAAAAAAAAJKAAAA+EAAC2z2Rlc2MAAAAAAAAAFklFQyBodHRwOi8vd3d3LmllYy5jaAAAAAAAAAAAAAAAFklFQyBodHRwOi8vd3d3LmllYy5jaAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABkZXNjAAAAAAAAAC5JRUMgNjE5NjYtMi4xIERlZmF1bHQgUkdCIGNvbG91ciBzcGFjZSAtIHNSR0IAAAAAAAAAAAAAAC5JRUMgNjE5NjYtMi4xIERlZmF1bHQgUkdCIGNvbG91ciBzcGFjZSAtIHNSR0IAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZGVzYwAAAAAAAAAsUmVmZXJlbmNlIFZpZXdpbmcgQ29uZGl0aW9uIGluIElFQzYxOTY2LTIuMQAAAAAAAAAAAAAALFJlZmVyZW5jZSBWaWV3aW5nIENvbmRpdGlvbiBpbiBJRUM2MTk2Ni0yLjEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAHZpZXcAAAAAABOk/gAUXy4AEM8UAAPtzAAEEwsAA1yeAAAAAVhZWiAAAAAAAEwJVgBQAAAAVx/nbWVhcwAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAo8AAAACc2lnIAAAAABDUlQgY3VydgAAAAAAAAQAAAAABQAKAA8AFAAZAB4AIwAoAC0AMgA3ADsAQABFAEoATwBUAFkAXgBjAGgAbQByAHcAfACBAIYAiwCQAJUAmgCfAKQAqQCuALIAtwC8AMEAxgDLANAA1QDbAOAA5QDrAPAA9gD7AQEBBwENARMBGQEfASUBKwEyATgBPgFFAUwBUgFZAWABZwFuAXUBfAGDAYsBkgGaAaEBqQGxAbkBwQHJAdEB2QHhAekB8gH6AgMCDAIUAh0CJgIvAjgCQQJLAlQCXQJnAnECegKEAo4CmAKiAqwCtgLBAssC1QLgAusC9QMAAwsDFgMhAy0DOANDA08DWgNmA3IDfgOKA5YDogOuA7oDxwPTA+AD7AP5BAYEEwQgBC0EOwRIBFUEYwRxBH4EjASaBKgEtgTEBNME4QTwBP4FDQUcBSsFOgVJBVgFZwV3BYYFlgWmBbUFxQXVBeUF9gYGBhYGJwY3BkgGWQZqBnsGjAadBq8GwAbRBuMG9QcHBxkHKwc9B08HYQd0B4YHmQesB78H0gflB/gICwgfCDIIRghaCG4IggiWCKoIvgjSCOcI+wkQCSUJOglPCWQJeQmPCaQJugnPCeUJ+woRCicKPQpUCmoKgQqYCq4KxQrcCvMLCwsiCzkLUQtpC4ALmAuwC8gL4Qv5DBIMKgxDDFwMdQyODKcMwAzZDPMNDQ0mDUANWg10DY4NqQ3DDd4N+A4TDi4OSQ5kDn8Omw62DtIO7g8JDyUPQQ9eD3oPlg+zD88P7BAJECYQQxBhEH4QmxC5ENcQ9RETETERTxFtEYwRqhHJEegSBxImEkUSZBKEEqMSwxLjEwMTIxNDE2MTgxOkE8UT5RQGFCcUSRRqFIsUrRTOFPAVEhU0FVYVeBWbFb0V4BYDFiYWSRZsFo8WshbWFvoXHRdBF2UXiReuF9IX9xgbGEAYZRiKGK8Y1Rj6GSAZRRlrGZEZtxndGgQaKhpRGncanhrFGuwbFBs7G2MbihuyG9ocAhwqHFIcexyjHMwc9R0eHUcdcB2ZHcMd7B4WHkAeah6UHr4e6R8THz4faR+UH78f6iAVIEEgbCCYIMQg8CEcIUghdSGhIc4h+yInIlUigiKvIt0jCiM4I2YjlCPCI/AkHyRNJHwkqyTaJQklOCVoJZclxyX3JicmVyaHJrcm6CcYJ0kneierJ9woDSg/KHEooijUKQYpOClrKZ0p0CoCKjUqaCqbKs8rAis2K2krnSvRLAUsOSxuLKIs1y0MLUEtdi2rLeEuFi5MLoIuty7uLyQvWi+RL8cv/jA1MGwwpDDbMRIxSjGCMbox8jIqMmMymzLUMw0zRjN/M7gz8TQrNGU0njTYNRM1TTWHNcI1/TY3NnI2rjbpNyQ3YDecN9c4FDhQOIw4yDkFOUI5fzm8Ofk6Njp0OrI67zstO2s7qjvoPCc8ZTykPOM9Ij1hPaE94D4gPmA+oD7gPyE/YT+iP+JAI0BkQKZA50EpQWpBrEHuQjBCckK1QvdDOkN9Q8BEA0RHRIpEzkUSRVVFmkXeRiJGZ0arRvBHNUd7R8BIBUhLSJFI10kdSWNJqUnwSjdKfUrESwxLU0uaS+JMKkxyTLpNAk1KTZNN3E4lTm5Ot08AT0lPk0/dUCdQcVC7UQZRUFGbUeZSMVJ8UsdTE1NfU6pT9lRCVI9U21UoVXVVwlYPVlxWqVb3V0RXklfgWC9YfVjLWRpZaVm4WgdaVlqmWvVbRVuVW+VcNVyGXNZdJ114XcleGl5sXr1fD19hX7NgBWBXYKpg/GFPYaJh9WJJYpxi8GNDY5dj62RAZJRk6WU9ZZJl52Y9ZpJm6Gc9Z5Nn6Wg/aJZo7GlDaZpp8WpIap9q92tPa6dr/2xXbK9tCG1gbbluEm5rbsRvHm94b9FwK3CGcOBxOnGVcfByS3KmcwFzXXO4dBR0cHTMdSh1hXXhdj52m3b4d1Z3s3gReG54zHkqeYl553pGeqV7BHtje8J8IXyBfOF9QX2hfgF+Yn7CfyN/hH/lgEeAqIEKgWuBzYIwgpKC9INXg7qEHYSAhOOFR4Wrhg6GcobXhzuHn4gEiGmIzokziZmJ/opkisqLMIuWi/yMY4zKjTGNmI3/jmaOzo82j56QBpBukNaRP5GokhGSepLjk02TtpQglIqU9JVflcmWNJaflwqXdZfgmEyYuJkkmZCZ/JpomtWbQpuvnByciZz3nWSd0p5Anq6fHZ+Ln/qgaaDYoUehtqImopajBqN2o+akVqTHpTilqaYapoum/adup+CoUqjEqTepqaocqo+rAqt1q+msXKzQrUStuK4trqGvFq+LsACwdbDqsWCx1rJLssKzOLOutCW0nLUTtYq2AbZ5tvC3aLfguFm40blKucK6O7q1uy67p7whvJu9Fb2Pvgq+hL7/v3q/9cBwwOzBZ8Hjwl/C28NYw9TEUcTOxUvFyMZGxsPHQce/yD3IvMk6ybnKOMq3yzbLtsw1zLXNNc21zjbOts83z7jQOdC60TzRvtI/0sHTRNPG1EnUy9VO1dHWVdbY11zX4Nhk2OjZbNnx2nba+9uA3AXcit0Q3ZbeHN6i3ynfr+A24L3hROHM4lPi2+Nj4+vkc+T85YTmDeaW5x/nqegy6LzpRunQ6lvq5etw6/vshu0R7ZzuKO6070DvzPBY8OXxcvH/8ozzGfOn9DT0wvVQ9d72bfb794r4Gfio+Tj5x/pX+uf7d/wH/Jj9Kf26/kv+3P9t//9BTFBI/gEAAAGQBEm2aVvr2bb1bdu2bdu2bdu2bXNm23q21udZe/fnMCImgP5zmmRu0r5916pB5r+K3/SXacyc8GRljl+j3BX++e1yv0LNd2z0QR48+5Ns/IAbXNlYAQ+BG8bS2z5os0SJVcBM14q4M1jdz6L4CmDTWfwpF1izFNEBe7CAx5IH+QjcbKVkNMHXSTJ2Mwte9g/GphB+0WhDKQ1+gdJxhrY6gmWoXyS4UbKRPV4EbGrm0O5BatSLG+kGnuYh3KBRW3adT2Bhak/CDbzIKq/U8LNBMRvDSqOjHh1q6IRR7K2a7xPPdnHVl6XjEdaZfmRoz9reWjwvs/7kG50sNFhtBWBO6GuizukUBEfUUNcvGYOveavK94ZB0zupmsKwx+3UeN/ACS+gpmMaDrdR4nKWgScraZ+K9HGUpcz6EENvspblfgu135fkYxl6BcndrmPd9pYVDMdKqiMrG4/F42UZn4KdtBVRm3Cs8JIyi2VYPEVGk8HWK1gKdtFZNgksrrJsOBgfsBMNRbvtLhqPdtpWYn8GbQFJA56htRc57AeLKiaiIuEoaenMnDTFUma9DmVZ+/kjW9ewJYX+M95BHAogjXU+AbwrRTpN1+l7Wd1EC4U279p/yMhxk2fNW7xi1Zo1a9auX7d23fpNGzesWbV07oyxfVoVJWSTn5uampiQRlZQOCCaAgAAcA4AnQEqQABAAD6RRp1LpaOioaQYCSCwEglnANAf6AeQHe3XstJbbZcWloaHR/56MDDk1JzbdWf27Soj3JHVF/BoubkvX8Bp3XzyR/oAldRu5TVjCGd9xVdUWuQc0BP47rzGCtAn6zv3wXHtB4bG9CSVD+oEq2pE0c7mAAD+/K1GfqGH49UVwpvCqjsxVhXg5o+M0D1wmzLC6U8M96RzqcqHYYL64nYfkP3NlmcIqUTADl4R/8Ztsmrt/8YGH4qXr2393zDsf2khD8UfXRv/zElSaeuqFGQzG+NapW+EPCWqxeGmGrucoYt0vuhR9z08U7tVe4smQtRrffH8AMzxnDkwsia9Q7ikGBk1Oc51vten/chX3UXHCp/q6ZYPSo4Kha5Xd2ZV4gBJ85FK0+VXYMTTqGW6OiTDUVdeXHR9njW6s1h24eZbsiPlutth9j3Ou5cllsXoG3L55dNM6Q5rptkxCVpvh922fZyK2tsmHdT+TLatnLfIlRXgwM5LFyx68u4BPdZNnN2utj4GjgF0Wa+WKgmRFL3o9gVgHJQ8P6Mmr9OjAjM7lXPSvRQPIYETWU8Cy6AhzyNC1w0NORNEZv5NuiejUtHF1CgehtJTM8JVjcsuccE709lBgCa7EsZLDXV+L2EcRNLXSoFEUVwn7KlWyM9voYncouQo+DZHd4uyaqvRMi0YwBIYNjywWIIGlGJjcxzQvuvEM08A6lEavQk149HoiRFqfwVyaaLGDV95XN/JC9XugBjdw5TPMaBo5GByVDmM9SaBS4iIRwlUGiSKRerUrlX5Y/pFCVsqbIsZ7a9YX+4mpCKphVCD7+mZyvqTtNnyqH32GRoJBGV/p5+HaWMuX9k4kyc1uy4r6+/36lLEkyFwQAAARVhJRmwAAABNTQAqAAAAEEV4aWZNZXRhAAUBGgAFAAAAAQAAAFIBGwAFAAAAAQAAAFoBKAADAAAAAQACAAABMQACAAAACgAAAGICEwADAAAAAQABAAAAAAAAAAAASAAAAAEAAABIAAAAAWV6Z2lmLmNvbQA=",
    system=(
        """
<SYSTEM_CAPABILITY>
You are an autonomous Android device control agent operating via ADB on a test device with full system access.
Your primary goal is to execute tasks efficiently and reliably while maintaining system stability.
</SYSTEM_CAPABILITY>

<CORE PRINCIPLES>
* Autonomy: Operate independently and make informed decisions without requiring user input.
* Never ask for other tasks to be done, only do the task you are given.
* Reliability: Ensure actions are repeatable and maintain system stability.
* Efficiency: Optimize operations to minimize latency and resource usage.
* Safety: Always verify actions before execution, even with full system access.
</CORE PRINCIPLES>

<OPERATIONAL GUIDELINES>
1. Tool Usage:
   * Verify tool availability before starting any operation
   * Use the most direct and efficient tool for each task
   * Combine tools strategically for complex operations
   * Prefer built-in tools over shell commands when possible

2. Error Handling:
   * Assess failures systematically: check tool availability, permissions, and device state
   * Implement retry logic with exponential backoff for transient failures
   * Use fallback strategies when primary approaches fail
   * Provide clear, actionable error messages with diagnostic information

3. Performance Optimization:
   * Use one-liner shell commands with inline filtering (grep, cut, awk, jq) for efficiency
   * Minimize screen captures and coordinate calculations
   * Cache device state information when appropriate
   * Batch related operations when possible

4. Screen Interaction:
   * Ensure all coordinates are integers and within screen bounds
   * Implement smart scrolling for off-screen elements
   * Use appropriate gestures (tap, swipe, drag) based on context
   * Verify element visibility before interaction

5. System Access:
   * Leverage full system access responsibly
   * Use shell commands for system-level operations
   * Monitor system state and resource usage
   * Maintain system stability during operations

6. Recovery Strategies:
   * If an element is not visible, try:
     - Scrolling in different directions
     - Adjusting view parameters
     - Using alternative interaction methods
   * If a tool fails:
     - Check device connection and state
     - Verify tool availability and permissions
     - Try alternative tools or approaches
   * If stuck:
     - Provide clear diagnostic information
     - Suggest potential solutions
     - Request user intervention only if necessary

7. Best Practices:
   * Document all significant operations
   * Maintain operation logs for debugging
   * Implement proper cleanup after operations
   * Follow Android best practices for UI interaction

<IMPORTANT NOTES>
* This is a test device with full system access - use this capability responsibly
* Always verify the success of critical operations
* Maintain system stability as the highest priority
* Provide clear, actionable feedback for all operations
* Use the most efficient method for each task
</IMPORTANT NOTES>
"""
    ),
    tools=[
        "android_screenshot_tool",
        "android_tap_tool",
        "android_type_tool",
        "android_drag_and_drop_tool",
        "android_key_event_tool",
        "android_swipe_tool",
        "android_key_combination_tool",
        "android_shell_tool",
        "android_connect_tool",
        "android_get_connected_devices_serial_numbers_tool",
        "android_get_connected_displays_infos_tool",
        "android_get_current_connected_device_infos_tool",
        "android_select_device_by_serial_number_tool",
        "android_select_display_by_index_tool",
        "android_setup_helper",
    ],
)

WEB_AGENT_V1 = AssistantV1(
    id="asst_68ac2c4edc4b2f27faa5a256",
    created_at=now_v1(),
    name="Web Agent",
    avatar="data:image/webp;base64,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",
    system=(
        """
<SYSTEM_CAPABILITY>
* You are utilizing a webbrowser in full-screen mode. So you are only seeing the content of the currently opened webpage (tab).
* It can be helpful to zoom in/out or scroll down/up so that you can see everything on the page. Make sure to that before deciding something isn't available.
* When using your tools, they take a while to run and send back to you. Where possible/feasible, try to chain multiple of these calls all into one function calls request.
* If a tool call returns with an error that a browser distribution is not found, stop, so that the user can install it and, then, continue the conversation.
</SYSTEM_CAPABILITY>
"""
    ),
    tools=[
        "browser_click",
        "browser_close",
        "browser_console_messages",
        "browser_drag",
        "browser_evaluate",
        "browser_file_upload",
        "browser_fill_form",
        "browser_handle_dialog",
        "browser_hover",
        "browser_navigate",
        "browser_navigate_back",
        "browser_network_requests",
        "browser_press_key",
        "browser_resize",
        "browser_select_option",
        "browser_snapshot",
        "browser_take_screenshot",
        "browser_type",
        "browser_wait_for",
        "browser_tabs",
        "browser_mouse_click_xy",
        "browser_mouse_drag_xy",
        "browser_mouse_move_xy",
        "browser_pdf_save",
        "browser_verify_element_visible",
        "browser_verify_list_visible",
        "browser_verify_text_visible",
        "browser_verify_value",
    ],
)

TESTING_AGENT_V1 = AssistantV1(
    id="asst_68ac2c4edc4b2f27faa5a257",
    created_at=now_v1(),
    name="Testing Agent",
    avatar="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB2aWV3Qm94PSIwIDAgMjcgMjciIGFyaWEtaGlkZGVuPSJ0cnVlIiByb2xlPSJpbWciIGNsYXNzPSJpY29uaWZ5IGljb25pZnktLXR3ZW1vamkiIHByZXNlcnZlQXNwZWN0UmF0aW89InhNaWRZTWlkIG1lZXQiPjxwYXRoIGZpbGw9IiNDQ0Q2REQiIGQ9Ik0xMC45MjIgMTAuODEgMTkuMTAyIDIuNjI5bDUuMjIxIDUuMjIxIC04LjE4MSA4LjE4MXoiLz48cGF0aCBmaWxsPSIjNjhFMDkwIiBkPSJNNi4wNzcgMjUuNzk5QzEuODc1IDI1LjUgMS4xMjUgMjIuNTQ3IDEuMjI2IDIwLjk0OWMwLjI0MSAtMy44MDMgMTEuNzAxIC0xMi40MTMgMTEuNzAxIC0xMi40MTNsOS4zODggMS40NDhjMC4wMDEgMCAtMTMuMDQyIDE2LjA0NCAtMTYuMjM3IDE1LjgxNiIvPjxwYXRoIGZpbGw9IiM4ODk5QTYiIGQ9Ik0yNC4yNDUgMi43ODFDMjIuMDU0IDAuNTkgMTkuNTc4IC0wLjQ4NyAxOC43MTUgMC4zNzdjLTAuMDEgMC4wMSAtMC4wMTcgMC4wMjMgLTAuMDI2IDAuMDMzIC0wLjAwNSAwLjAwNSAtMC4wMTEgMC4wMDYgLTAuMDE2IDAuMDExTDEuNzIxIDE3LjM3M2E1LjU3MiA1LjU3MiAwIDAgMCAtMS42NDMgMy45NjZjMCAxLjQ5OCAwLjU4NCAyLjkwNiAxLjY0MyAzLjk2NWE1LjU3MiA1LjU3MiAwIDAgMCAzLjk2NiAxLjY0MyA1LjU3MiA1LjU3MiAwIDAgMCAzLjk2NSAtMS42NDJsMTYuOTUzIC0xNi45NTNjMC4wMDUgLTAuMDA1IDAuMDA3IC0wLjAxMiAwLjAxMSAtMC4wMTcgMC4wMSAtMC4wMDkgMC4wMjIgLTAuMDE1IDAuMDMyIC0wLjAyNSAwLjg2MyAtMC44NjIgLTAuMjE0IC0zLjMzOCAtMi40MDUgLTUuNTI5TTguMDYzIDIzLjcxNGMtMC42MzQgMC42MzQgLTEuNDc4IDAuOTgzIC0yLjM3NCAwLjk4M3MtMS43NDEgLTAuMzUgLTIuMzc1IC0wLjk4NGEzLjMzOCAzLjMzOCAwIDAgMSAtMC45ODQgLTIuMzc1YzAgLTAuODk3IDAuMzUgLTEuNzQgMC45ODMgLTIuMzc0TDE5LjA1OSAzLjIxOGMwLjQ2NyAwLjg1OCAxLjE3IDEuNzk2IDIuMDYyIDIuNjg4czEuODMgMS41OTUgMi42ODggMi4wNjJ6Ii8+PHBhdGggZmlsbD0iIzE3QkY2MyIgZD0iTTIxLjg5NyA5Ljg1OGMtMC4wNDQgMC4yODQgLTEuOTcgMC41NjMgLTQuMjY4IDAuMjU3cy00LjExMiAtMC45MTcgLTQuMDUyIC0xLjM2NSAxLjk3IC0wLjU2MyA0LjI2OCAtMC4yNTcgNC4xMjEgMC45MTggNC4wNTIgMS4zNjVNOC4xMyAxNy40MzVhMC41OTYgMC41OTYgMCAxIDEgLTAuODQyIC0wLjg0MyAwLjU5NiAwLjU5NiAwIDAgMSAwLjg0MiAwLjg0M20yLjQ4OCAxLjk2MWEwLjk3NCAwLjk3NCAwIDEgMSAtMS4zNzYgLTEuMzc3IDAuOTc0IDAuOTc0IDAgMCAxIDEuMzc2IDEuMzc3bTEuMjU4IC0zLjk5M2EwLjkxNiAwLjkxNiAwIDAgMSAtMS4yOTQgLTEuMjk0IDAuOTE1IDAuOTE1IDAgMSAxIDEuMjk0IDEuMjk0bS01LjE1MSA2LjY0NGExLjExNyAxLjExNyAwIDEgMSAtMS41NzkgLTEuNTc5IDEuMTE3IDEuMTE3IDAgMCAxIDEuNTc5IDEuNTc5bTguNTQ3IC02Ljg2OGEwLjc5NCAwLjc5NCAwIDEgMSAtMS4xMjIgLTEuMTIzIDAuNzk0IDAuNzk0IDAgMCAxIDEuMTIyIDEuMTIzbS0wLjkwNSAtMy4yMTZhMC41MiAwLjUyIDAgMSAxIC0wLjczNCAtMC43MzUgMC41MiAwLjUyIDAgMCAxIDAuNzM0IDAuNzM1Ii8+PHBhdGggdHJhbnNmb3JtPSJyb3RhdGUoLTQ1LjAwMSAzMC44MTcgNS4yMjMpIiBmaWxsPSIjQ0NENkREIiBjeD0iMzAuODE3IiBjeT0iNS4yMjMiIHJ4PSIxLjE4NCIgcnk9IjQuODQ3IiBkPSJNMjQuMDAxIDMuOTE3QTAuODg4IDMuNjM1IDAgMCAxIDIzLjExMyA3LjU1M0EwLjg4OCAzLjYzNSAwIDAgMSAyMi4yMjUgMy45MTdBMC44ODggMy42MzUgMCAwIDEgMjQuMDAxIDMuOTE3eiIvPjwvc3ZnPg==",
    system=(
        """
You are an advanced AI testing agent responsible for managing and executing software tests. Your primary goal is to create, refine, and execute test scenarios based on given specifications or targets. You have access to various tools and subagents to accomplish this task.

Available tools:
1. Feature management: retrieve, list, modify, create, delete
2. Scenario management: retrieve, list, modify, create, delete
3. Execution management: retrieve, list, modify, create, delete
4. Tools for executing tests using subagents:
   - create_thread_and_run_v1_runs_post: Delegate tasks to subagents
   - retrieve_run_v1_threads: Check the status of a run
   - list_messages_v1_threads: Retrieve messages from a thread
   - utility_wait: Wait for a specified number of seconds

Subagents:
1. Computer control agent (ID: asst_68ac2c4edc4b2f27faa5a253)
2. Web browser control agent (ID: asst_68ac2c4edc4b2f27faa5a256)

Main process:
1. Analyze test specification
2. Create and refine features if necessary by exploring the features (exploratory testing)
3. Create and refine scenarios if necessary by exploring the scenarios (exploratory testing)
4. Execute scenarios
5. Report results
6. Handle user feedback

Detailed instructions:

1. Analyze the test specification:
<test_specification>
{TEST_SPECIFICATION}
</test_specification>

Review the provided test specification carefully. Identify the key features, functionalities, or areas that need to be tested.
Instead of a test specification, the user may also provide just the testing target (feature, url, application name etc.). Make
sure that you ask the user if it is a webapp or desktop app or where to find the app in general if not clear from the specification.

2. Create and refine features:
a. Use the feature management tools to list existing features.
b. Create new features based on user input and if necessary exploring the features in the actual application using a subagent, ensuring no duplicates.
c. Present the features to the user and wait for feedback.
d. Refine the features based on user feedback until confirmation is received.

3. Create and refine scenarios:
a. For each confirmed feature, use the scenario management tools to list existing scenarios.
b. Create new scenarios using Gherkin syntax, ensuring no duplicates.
c. Present the scenarios to the user and wait for feedback.
d. Refine the scenarios based on user feedback until confirmation is received.

4. Execute scenarios:
a. Determine whether to use the computer control agent or web browser control agent (prefer web browser if possible).
b. Create and run a thread with the chosen subagent with a user message that contains the commands (scenario) to be executed. Set `stream` to `false` to wait for the agent to complete.
c. Use the retrieve_run_v1_threads tool to check the status of the task and the utility_wait tool for it to complete with an exponential backoff starting with 5 seconds increasing.
d. Collect and analyze the responses from the agent using the list_messages_v1_threads tool. Usually, you only need the last message within the thread (`limit=1`) which contains a summary of the execution results. If you need more details, you can use a higher limit and potentially multiple calls to the tool.

5. Report results:
a. Use the execution management tools to create new execution records.
b. Update the execution records with the results (passed, failed, etc.).
c. Present a summary of the execution results to the user.

6. Handle user feedback:
a. Review user feedback on the executions.
b. Based on feedback, determine whether to restart the process, modify existing tests, or perform other actions.

Handling user commands:
Respond appropriately to user commands, such as:
<user_command>
{USER_COMMAND}
</user_command>

- Execute existing scenarios
- List all available features
- Modify specific features or scenarios
- Delete features or scenarios

Output format (for none tool calls):
```
[Your detailed response, including any necessary explanations, lists, or summaries]

**Next Actions**:
[Clearly state the next actions you will take or the next inputs you require from the user]
</next_action>
```

Important reminders:
1. Always check for existing features and scenarios before creating new ones to avoid duplicates.
2. Use Gherkin syntax when creating or modifying scenarios.
3. Prefer the web browser control agent for test execution when possible.
4. Always wait for user confirmation before proceeding to the next major step in the process.
5. Be prepared to restart the process or modify existing tests based on user feedback.
6. Use tags for organizing the features and scenarios describing what is being tested and how it is being tested.
7. Prioritize sunny cases and critical features/scenarios first if not specified otherwise by the user.

Your final output should only include the content within the <response> and <next_action> tags. Do not include any other tags or internal thought processes in your final output.
"""
    ),
    tools=[
        "create_feature",
        "retrieve_feature",
        "list_features",
        "modify_feature",
        "delete_feature",
        "create_scenario",
        "retrieve_scenario",
        "list_scenarios",
        "modify_scenario",
        "delete_scenario",
        "create_execution",
        "retrieve_execution",
        "list_executions",
        "modify_execution",
        "delete_execution",
        "create_thread_and_run_v1_runs_post",
        "retrieve_run_v1_threads",
        "utility_wait",
        "list_messages_v1_threads",
    ],
)

ORCHESTRATOR_AGENT_V1 = AssistantV1(
    id="asst_68ac2c4edc4b2f27faa5a258",
    created_at=now_v1(),
    name="Orchestrator",
    avatar="data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTIgOFY0SDgiIC8+CiAgPHJlY3Qgd2lkdGg9IjE2IiBoZWlnaHQ9IjEyIiB4PSI0IiB5PSI4IiByeD0iMiIgLz4KICA8cGF0aCBkPSJNMiAxNGgyIiAvPgogIDxwYXRoIGQ9Ik0yMCAxNGgyIiAvPgogIDxwYXRoIGQ9Ik0xNSAxM3YyIiAvPgogIDxwYXRoIGQ9Ik05IDEzdjIiIC8+Cjwvc3ZnPgo=",
    system=(
        """
You are an AI agent called "Orchestrator" with the ID "asst_68ac2c4edc4b2f27faa5a258". Your primary role is to perform high-level planning and management of all tasks involved in responding to a given prompt. For simple prompts, you will respond directly. For more complex, you will delegate and route the execution of these tasks to other specialized agents.

You have the following tools at your disposal:

1. list_assistants_v1_assistants_get
   This tool enables you to discover all available assistants (agents) for task delegation.

2. create_thread_and_run_v1_runs_post
   This tool enables you to delegate tasks to other agents by starting a conversation (thread) with initial messages containing necessary instructions, and then running (calling/executing) the agent to get a response. The "stream" parameter should always be set to "false".

3. retrieve_run_v1_threads
   This tool enables you to retrieve the details of a run by its ID and, by that, checking wether an assistant is still answering or completed its answer (`status` field).

4. list_messages_v1_threads
   This tool enables you to retrieve the messages of the assistant. Depending on the prompt, you may only need the last message within the thread (`limit=1`) or the whole thread using a higher limit and potentially multiple calls to the tool.

5. utility_wait
   This tool enables you to wait for a specified number of seconds, e.g. to wait for an agent to finish its task / complete its answer.

Your main task is to analyze the user prompt and classify it as simple vs. complex. For simple prompts, respond directly. For complex prompts, create a comprehensive plan to address it by utilizing the available agents.

Follow these steps to complete your task:

1. Analyze the user prompt and identify the main components or subtasks required to provide a complete response.

2. Use the list_assistants_v1_assistants_get tool to discover all available agents.

3. Create a plan that outlines how you will delegate these subtasks to the most appropriate agents based on their specialties.

4. For each subtask:
   a. Prepare clear and concise instructions for the chosen agent.
   b. Use the create_thread_and_run_v1_runs_post tool to delegate the task to the agent.
   c. Include all necessary context and information in the initial messages.
   d. Set the "stream" parameter to "true".

5. Use the retrieve_run_v1_threads tool to check the status of the task and the utility_wait tool for it to complete with an exponential backoff starting with 5 seconds increasing.

5. Collect and analyze the responses from each agent using the list_messages_v1_threads tool.

6. Synthesize the information from all agents into a coherent and comprehensive response to the original user prompt.

Present your final output should be eitehr in the format of

[Simple answer]

or

[
# Plan
[Provide a detailed plan outlining the subtasks and the agents assigned to each]

# Report
[For each agent interaction, include:
1. The agent's ID and specialty
2. The subtask assigned
3. A summary of the instructions given
4. A brief summary of the agent's response]

# Answer
[Synthesize all the information into a cohesive response to the original user prompt]
]
"""
    ),
    tools=[
        "list_assistants_v1_assistants_get",
        "create_thread_and_run_v1_runs_post",
        "retrieve_run_v1_threads",
        "utility_wait",
        "list_messages_v1_threads",
    ],
)

SEEDS_V1 = [
    COMPUTER_AGENT_V1,
    ANDROID_AGENT_V1,
    WEB_AGENT_V1,
]

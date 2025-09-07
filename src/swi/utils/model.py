import os
from rich.console import Console
from rich.prompt import Prompt
from swi.utils.config import ENV_FILE
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

console = Console()


# Base class for all models
class BaseModelLoader:
    def load(self):
        """Return a model instance. Must be implemented by subclasses."""
        raise NotImplementedError
    def check(self):
        """Checks if the model keys are present"""
        raise NotImplementedError

    def find_missing(self):
        """Checks for all missing env var"""
        missing = [var for var in self.required_env_vars if not os.getenv(var)]
        self.ask(missing)    
    
    def ask(self, missing):
        """Ask for the missing variables and then stores them in a .env"""
        for count in range(3):
            """Try 3 times if the key value entered are not valid"""
            for key in missing:
                value = Prompt.ask(f"Enter {key} value")
                with open(ENV_FILE,"a") as f:
                    f.write(f"{key}={value}\n")
                    os.environ[key] = value
            if self.check():
                break 
            console.print("[bold red]alert![/bold red] The key entered is not valid Try again !!!")    
            if count == 2:
                exit()
# ------------------------
# Provider-specific classes
# ------------------------
class AzureOpenAILoader(BaseModelLoader):
    required_env_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "OPENAI_API_VERSION"
    ]

    
    def check(self):
        try:
            from openai import AzureOpenAI
            client = AzureOpenAI(api_key=os.getenv('AZURE_OPENAI_API_KEY'), azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),api_version=os.getenv("OPENAI_API_VERSION"))
            client.models.list()
            return True
        except ImportError:
            console.print("You dont have openai installed")
            exit()
        except Exception:
            console.print_exception()
            return False

        
    def load(self):
        from langchain_openai import AzureChatOpenAI
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not api_key or not endpoint:
            raise RuntimeError("Missing AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT")
        return AzureChatOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT", "default"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-05-01-preview"),
            temperature=0,
            azure_deployment = os.getenv("AZURE_DEPLOYMENT","gpt-4o-mini")
        )


class GroqLoader(BaseModelLoader):
    required_env_vars = [
        "GROQ_API_KEY"
    ]
    
    def check(self):
        try:
            from groq import Groq
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            client.models.list()
            return True
        except ImportError:
            console.print("You dont have openai installed")
            exit()
        except Exception:
            return False

    def load(self):
        from langchain_groq import ChatGroq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GROQ_API_KEY")
        return ChatGroq(
            groq_api_key=api_key,
            model=os.getenv("GROQ_MODEL", "mixtral-8x7b-32768"),
            temperature=0
        )


class OpenAILoader(BaseModelLoader):

    def check(self):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            client.models.list()
            return True
        except ImportError:
            console.print("You dont have openai installed")
            exit()
        except Exception:
            return False

    def load(self):
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY")
        return ChatOpenAI(
            api_key=api_key,
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=0
        )


# ------------------------
# Main loader (registry)
# ------------------------
class ModelLoader:
    """Extensible model loader using provider classes."""
    def __init__(self):
        self.console = console
        self.providers = {
            "azure-openai": AzureOpenAILoader(),
            "groq": GroqLoader(),
            "openai": OpenAILoader(),
            # Add more model if need it
        }
        
    def check(self, provider_name: str = None):
        provider_name: str = self._detect_model()
        if provider_name:
            if provider_name not in self.providers:
                raise ValueError(f"Provider {provider_name} not registered")
            if self.providers[provider_name].check():
                return True
            self.providers[provider_name].find_missing()
        else:
            return False


    def _detect_model(self) -> str:
        """Detect available model backend (azure_openai, groq, openai).
           Returns model name as string, or raises error if not found.
        """
        if os.getenv("PROVIDER"):
            return os.getenv("PROVIDER") 
        available_packages = ["azure-openai","openai","groq"]
        # Priority order (you can change it)
        # Display nice table of choices
        table = Table(title="Available Model Backends", show_header=True, header_style="bold magenta")
        table.add_column("Index", justify="center")
        table.add_column("Provider", justify="left")

        for idx, provider in enumerate(available_packages, start=1):
            table.add_row(str(idx), provider)

        console.print(table)

        # Ask user to choose
        while True:
            choice = Prompt.ask(
                "[bold green]Enter the index of the model you want to use[/]",
                choices=[str(i) for i in range(1, len(available_packages)+1)]
            )
            selected = available_packages[int(choice)-1]
            console.print(f"[cyan]You selected:[/cyan] {selected}")
            with open(ENV_FILE,"a") as f:
                f.write(f"PROVIDER={selected}\n")
            return selected


            
    def load(self):
        """
        Load model by provider name.
        If provider_name is None, pick the first available with valid keys.
        """
        provider_name: str = self._detect_model()
        if provider_name:
            if provider_name not in self.providers:
                raise ValueError(f"Provider {provider_name} not registered")
            return self.providers[provider_name].load()

        # Auto-select first provider with valid keys
        for name, loader in self.providers.items():
            try:
                model = loader.load()
                self.console.print(f"[cyan]Loaded model from {name}[/]")
                return model
            except Exception:
                continue

        raise RuntimeError("⚠️ No valid provider found")


# ------------------------
# Example usage
# ------------------------
if __name__ == "__main__":
    loader = ModelLoader()
    model = loader.load()  # Auto-select first available
    print("✅ Loaded model:", model)

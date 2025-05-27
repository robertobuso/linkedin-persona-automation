"""
Prompt builder utilities for LinkedIn Presence Automation Application.

Provides utilities for building structured prompts for AI services
with template management and dynamic content insertion.
"""

import logging
from typing import Dict, Any, Optional, List
from string import Template

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    Utility class for building structured prompts for AI services.

    Provides template management and dynamic content insertion for
    consistent prompt generation across different AI operations.
    """

    def __init__(self):
        """Initialize prompt builder with default templates."""
        self.templates = {
            "summarization": Template("""
Please summarize the following content for a LinkedIn audience.

CONTENT TO SUMMARIZE:
$content

USER TONE PROFILE:
$tone_context

REQUIREMENTS:
- Maximum summary length: $max_length words
- Extract 3-5 key points that provide professional value
- Match the user's communication style described above
- Focus on insights relevant to LinkedIn professionals
- Ensure the summary is engaging and actionable

Please provide a summary that captures the essence of the content while matching the user's professional communication style.
            """),
            
            "post_generation": Template("""
Please create a LinkedIn post based on the following content summary.

CONTENT SUMMARY:
$summary

USER TONE PROFILE:
$tone_context

POST STYLE GUIDANCE:
$style_guidance

USER WRITING EXAMPLES:
$examples_context

REQUIREMENTS:
- Create an engaging LinkedIn post (150-300 words)
- Match the user's communication style shown in examples
- Follow the specified post style guidance
- Include 3-5 relevant hashtags
- Add engagement elements (questions, calls-to-action)
- Use proper formatting with line breaks for readability
- Ensure professional value and authenticity
- Start with a compelling hook
- End with engagement-driving element

Please generate a LinkedIn post that captures the essence of the content while matching the user's authentic voice and style.
            """),
            
            "comment_generation": Template("""
Please generate a thoughtful comment for the following LinkedIn post.

POST CONTENT:
$post_content

POST AUTHOR: $post_author

USER TONE PROFILE:
$tone_context

ENGAGEMENT TYPE: $engagement_type

REQUIREMENTS:
- Maximum comment length: $max_length characters
- Match the user's communication style
- Be relevant and add value to the conversation
- Maintain professional tone appropriate for LinkedIn
- Avoid generic responses
- Show genuine engagement with the content

Please generate a comment that demonstrates thoughtful engagement while maintaining the user's authentic voice.
            """)
        }

    def build_prompt(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Build a prompt using a template and variables.

        Args:
            template_name: Name of the template to use
            variables: Dictionary of variables to substitute

        Returns:
            Built prompt string

        Raises:
            ValueError: If template not found or variables missing
        """
        try:
            if template_name not in self.templates:
                raise ValueError(f"Template '{template_name}' not found")

            template = self.templates[template_name]
            
            # Validate required variables
            template_vars = self._extract_template_variables(template.template)
            missing_vars = [var for var in template_vars if var not in variables]
            
            if missing_vars:
                logger.warning(f"Missing variables for template '{template_name}': {missing_vars}")
                # Provide default values for missing variables
                for var in missing_vars:
                    variables[var] = f"[{var} not provided]"

            # Substitute variables
            prompt = template.safe_substitute(variables)
            
            # Clean up the prompt
            prompt = self._clean_prompt(prompt)
            
            logger.debug(f"Built prompt for template '{template_name}': {len(prompt)} characters")
            return prompt

        except Exception as e:
            logger.error(f"Failed to build prompt for template '{template_name}': {str(e)}")
            raise ValueError(f"Prompt building failed: {str(e)}")

    def _extract_template_variables(self, template_string: str) -> List[str]:
        """
        Extract variable names from template string.

        Args:
            template_string: Template string with $variable placeholders

        Returns:
            List of variable names
        """
        import re
        
        # Find all $variable patterns
        pattern = r'\$([a-zA-Z_][a-zA-Z0-9_]*)'
        variables = re.findall(pattern, template_string)
        
        return list(set(variables))

    def _clean_prompt(self, prompt: str) -> str:
        """
        Clean and format the prompt.

        Args:
            prompt: Raw prompt string

        Returns:
            Cleaned prompt string
        """
        # Remove excessive whitespace
        lines = prompt.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip whitespace but preserve intentional indentation
            cleaned_line = line.rstrip()
            cleaned_lines.append(cleaned_line)
        
        # Remove excessive blank lines
        result_lines = []
        prev_blank = False
        
        for line in cleaned_lines:
            is_blank = not line.strip()
            
            if is_blank and prev_blank:
                continue  # Skip consecutive blank lines
            
            result_lines.append(line)
            prev_blank = is_blank
        
        # Join and strip final result
        return '\n'.join(result_lines).strip()

    def add_template(self, name: str, template_string: str) -> None:
        """
        Add a new template.

        Args:
            name: Template name
            template_string: Template string with $variable placeholders
        """
        try:
            self.templates[name] = Template(template_string)
            logger.info(f"Added template '{name}'")
        except Exception as e:
            logger.error(f"Failed to add template '{name}': {str(e)}")
            raise ValueError(f"Invalid template: {str(e)}")

    def get_template_variables(self, template_name: str) -> List[str]:
        """
        Get list of variables required by a template.

        Args:
            template_name: Name of the template

        Returns:
            List of required variable names

        Raises:
            ValueError: If template not found
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        template = self.templates[template_name]
        return self._extract_template_variables(template.template)

    def list_templates(self) -> List[str]:
        """
        Get list of available template names.

        Returns:
            List of template names
        """
        return list(self.templates.keys())

    def validate_template_variables(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that all required variables are provided.

        Args:
            template_name: Name of the template
            variables: Variables to validate

        Returns:
            Validation result with missing variables and suggestions

        Raises:
            ValueError: If template not found
        """
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        required_vars = self.get_template_variables(template_name)
        provided_vars = list(variables.keys())
        
        missing_vars = [var for var in required_vars if var not in provided_vars]
        extra_vars = [var for var in provided_vars if var not in required_vars]

        return {
            "valid": len(missing_vars) == 0,
            "required_variables": required_vars,
            "provided_variables": provided_vars,
            "missing_variables": missing_vars,
            "extra_variables": extra_vars
        }
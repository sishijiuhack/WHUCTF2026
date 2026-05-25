<?php
if (isset($_SERVER['SCRIPT_FILENAME']) && realpath($_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    highlight_file(__FILE__);
}

// 下面这批类是兼容旧版本遗留的数据结构。
class Banner
{
    public $title = 'Elephant Image Station';
    public $subtitle = 'legacy mode';
}

class Profile
{
    public $name = 'guest';
    public $avatar = 'default.jpg';
}

class FileRecord
{
    public $path = '';
    public $size = 0;
}

class AuditLog
{
    public $message = '';

    public function append($line)
    {
        $this->message .= $line;
    }
}

class Visitor
{
    public $username = 'guest';
    public $bio;

    public function __destruct()
    {
        if ($this->bio) {
            echo $this->bio;
        }
    }
}

class ShowCard
{
    public $source;

    public function __toString()
    {
        if (!is_object($this->source)) {
            return 'empty';
        }

        $resolver = $this->source;
        return (string)$resolver();
    }
}

class LabelResolver
{
    public $entry;
    public $field = 'label';

    public function __invoke()
    {
        if (!is_object($this->entry)) {
            return 'empty';
        }

        return $this->entry->{$this->field};
    }
}

class CacheEntry
{
    public $driver;
    public $cacheKey = '';
    public $method = 'render';

    public function __get($name)
    {
        if (!is_object($this->driver)) {
            return 'cache-miss';
        }

        return $this->driver->{$this->method}($this->cacheKey);
    }
}

class TemplateEngine
{
    public $shell = '';

    public function __call($name, $arguments)
    {
        if (!preg_match('/[A-Za-z0-9!%~$]/is', $this->shell)) {
            eval($this->shell);
        } else {
            echo 'Hacker!';
        }

        return '';
    }
}

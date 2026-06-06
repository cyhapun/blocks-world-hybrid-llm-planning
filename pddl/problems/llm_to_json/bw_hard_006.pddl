(define (problem bw_hard_006)
  (:domain blocks-world)

  (:objects
    a b c d e - block
  )

  (:init
    (on_table e)
    (on_table a)
    (on_table b)
    (on d e)
    (on c d)
    (clear c)
    (clear a)
    (clear b)
    (handempty)
  )

  (:goal
    (and
      (on a c)
      (on b a)
    )
  )
)
